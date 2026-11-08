import asyncio
import json
import signal
import statistics
import time

import conversation_addressee
import listener_runtime
import transcript_log
from agent_route import ask_agent
from gpt_live import GptLive
from live_events import AssistantSaid, Audio, Failed, TaskRequested, Usage, UserSaid
from room_audio import Speaker, microphone_chunks
from spoken_turns import Party, TurnAssembler

BARGE_IN_BUFFER_SECONDS = 0.4
TURN_SETTLE_SECONDS = 1.2
TURN_CHECK_SECONDS = 0.2
WAKE_HANDOVER_SECONDS = 0.6
CLOSE_TIMEOUT_SECONDS = 5
DRAIN_TIMEOUT_SECONDS = 10
NOBODY_HOLDS_THE_ROOM = "No agent holds the room right now, so nobody can do that."


class LiveConversation:
    def __init__(self, voice, directory, speaker):
        self.voice = voice
        self.directory = directory
        self.transcript = directory / "transcript.jsonl"
        self.speaker = speaker
        self.turns = TurnAssembler(TURN_SETTLE_SECONDS)
        self.handoffs = set()
        self.last_user_text_at = None
        self.waiting_for_first_audio = False
        self.answer_latencies = []
        self.usage = {}
        self.event_handlers = {
            Audio: self.play,
            UserSaid: self.hear_user,
            AssistantSaid: self.record_assistant_speech,
            TaskRequested: self.start_hand_off,
            Usage: self.record_usage,
            Failed: self.report_failure,
        }

    def write(self, finished_turns):
        for turn in finished_turns:
            if turn.party is Party.HUMAN:
                transcript_log.append(self.transcript, Party.HUMAN, turn.text)
            else:
                transcript_log.append(
                    self.transcript, Party.AVATAR, turn.text, speaker=Party.AVATAR
                )
            print(f"{turn.party}: {turn.text}", flush=True)

    async def stream_microphone(self):
        async for chunk in microphone_chunks(self.voice.input_rate):
            await self.voice.send_audio(chunk)

    async def settle_turns(self):
        while True:
            await asyncio.sleep(TURN_CHECK_SECONDS)
            self.write(self.turns.settled(time.monotonic()))

    async def handle_events(self):
        async for event in self.voice.events():
            handler = self.event_handlers.get(type(event))
            if handler:
                handler(event)

    def record_assistant_speech(self, event):
        self.write(self.turns.add(Party.AVATAR, event.text, time.monotonic()))

    def start_hand_off(self, event):
        self.write(self.turns.finish())
        handoff = asyncio.create_task(self.hand_off(event))
        self.handoffs.add(handoff)
        handoff.add_done_callback(self.handoffs.discard)

    def record_usage(self, event):
        self.usage = event.details

    def report_failure(self, event):
        print(f"error: {event.message}", flush=True)

    def play(self, audio):
        if self.waiting_for_first_audio and audio.voiced():
            self.answer_latencies.append(time.monotonic() - self.last_user_text_at)
            self.waiting_for_first_audio = False
        self.speaker.play(audio.pcm)

    def hear_user(self, event):
        self.write(self.turns.add(Party.HUMAN, event.text, time.monotonic()))
        self.last_user_text_at = time.monotonic()
        self.waiting_for_first_audio = True
        if self.speaker.buffered_seconds() > BARGE_IN_BUFFER_SECONDS:
            self.speaker.clear()

    async def hand_off(self, task):
        await asyncio.sleep(WAKE_HANDOVER_SECONDS)
        holder = conversation_addressee.current(self.directory)
        if holder is None:
            await self.voice.deliver(task.task_id, NOBODY_HOLDS_THE_ROOM, True)
            return
        print(f"task for {holder.servant} at {holder.pane}: {task.request}", flush=True)
        answer = await ask_agent(holder.pane, task.request)
        await self.voice.deliver(task.task_id, answer.text, True)
        print(
            f"{holder.servant} answered in {answer.seconds} s: {answer.text}",
            flush=True,
        )

    def summary(self):
        latencies = sorted(self.answer_latencies)
        return {
            "provider": self.voice.name,
            "answers": len(latencies),
            "median_first_audio_s": round(statistics.median(latencies), 2)
            if latencies
            else None,
            "usage": self.usage,
        }


def stop_event_set_by_signals():
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        loop.add_signal_handler(number, stop.set)
    return stop


async def shut_down(voice, conversation, events, workers):
    try:
        await asyncio.wait_for(voice.close(), CLOSE_TIMEOUT_SECONDS)
        await asyncio.wait_for(events, DRAIN_TIMEOUT_SECONDS)
    except (OSError, TimeoutError):
        pass
    for task in [*workers, *conversation.handoffs]:
        task.cancel()
    conversation.write(conversation.turns.finish())
    conversation.speaker.close()
    print(json.dumps(conversation.summary(), ensure_ascii=False), flush=True)


async def run():
    voice = GptLive()
    session = await voice.connect()
    conversation = LiveConversation(
        voice, listener_runtime.runtime_directory(), Speaker(voice.output_rate)
    )
    print(f"{voice.name} live, session {session}", flush=True)
    stop = stop_event_set_by_signals()
    events = asyncio.create_task(conversation.handle_events())
    workers = [
        asyncio.create_task(conversation.stream_microphone()),
        asyncio.create_task(conversation.settle_turns()),
        events,
    ]
    stopped = asyncio.create_task(stop.wait())
    done, _ = await asyncio.wait(
        [stopped, *workers], return_when=asyncio.FIRST_COMPLETED
    )
    failures = [task.exception() for task in done if task is not stopped]
    await shut_down(voice, conversation, events, workers)
    for failure in failures:
        if failure:
            raise failure


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
