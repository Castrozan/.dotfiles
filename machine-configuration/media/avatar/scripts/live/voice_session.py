import asyncio

import live_voice
import transcript_log
from live_events import TaskRequested
from spoken_turns import Party, SpokenTurn

EARLIER_CONVERSATION_CHARACTERS = 12000
EARLIER_CONVERSATION_TURNS = 128
HOLDER_CHECK_SECONDS = 0.5


def spoken_turn(entry):
    if Party.AVATAR in (entry["source"], entry["speaker"]):
        return SpokenTurn(Party.AVATAR, entry["text"])
    speaker = entry["speaker"]
    return SpokenTurn(
        Party.HUMAN, f"{speaker}: {entry['text']}" if speaker else entry["text"]
    )


def earlier_conversation(transcript):
    turns = [spoken_turn(entry) for entry in transcript_log.read_since(transcript, 0)]
    kept, characters = [], 0
    for turn in reversed(turns[-EARLIER_CONVERSATION_TURNS:]):
        characters += len(turn.text)
        if characters > EARLIER_CONVERSATION_CHARACTERS:
            break
        kept.append(turn)
    return kept[::-1]


class RoomVoice:
    def __init__(self, open_voice, speaking_voice):
        self.open_voice = open_voice
        self.current = open_voice(speaking_voice, ())
        self.name = self.current.name
        self.input_rate = self.current.input_rate
        self.output_rate = self.current.output_rate
        self.task_owners = {}

    @property
    def speaking_voice(self):
        return self.current.speaking_voice

    async def connect(self):
        return await self.current.connect()

    async def change_to(self, speaking_voice, conversation_so_far):
        replacement = self.open_voice(speaking_voice, conversation_so_far)
        await replacement.connect()
        previous, self.current = self.current, replacement
        await previous.retire()

    async def follow_the_room_holder(self, directory, transcript, after_change):
        while True:
            await asyncio.sleep(HOLDER_CHECK_SECONDS)
            wanted = live_voice.holder_voice(directory)
            if wanted and wanted != self.speaking_voice:
                await self.change_to(wanted, earlier_conversation(transcript))
                after_change()

    def remember_task_owner(self, voice, event):
        if isinstance(event, TaskRequested):
            self.task_owners[event.task_id] = voice

    async def events_while_current(self, voice):
        async for event in voice.events():
            if voice is self.current:
                self.remember_task_owner(voice, event)
                yield event

    async def events(self):
        while True:
            voice = self.current
            async for event in self.events_while_current(voice):
                yield event
            if voice is self.current:
                return

    async def send_audio(self, pcm):
        await self.current.send_audio(pcm)

    async def deliver(self, task_id, result, final):
        owner = self.task_owners.get(task_id, self.current)
        if final:
            self.task_owners.pop(task_id, None)
        if owner is not self.current:
            task_id = None
        await self.current.deliver(task_id, result, final)

    async def close(self):
        await self.current.close()
