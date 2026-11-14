import asyncio

import live_voice
import transcript_log
from live_events import TaskRequested

EARLIER_CONVERSATION_CHARACTERS = 6000
HOLDER_CHECK_SECONDS = 0.5


def earlier_conversation(transcript):
    lines = [
        f"{entry['speaker'] or entry['source']}: {entry['text']}"
        for entry in transcript_log.read_since(transcript, 0)
    ]
    return "\n".join(lines)[-EARLIER_CONVERSATION_CHARACTERS:]


class RoomVoice:
    def __init__(self, open_voice, speaking_voice):
        self.open_voice = open_voice
        self.current = open_voice(speaking_voice, "")
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
        await previous.close()

    async def follow_the_room_holder(self, directory, transcript, after_change):
        while True:
            await asyncio.sleep(HOLDER_CHECK_SECONDS)
            wanted = live_voice.holder_voice(directory)
            if wanted and wanted != self.speaking_voice:
                await self.change_to(wanted, earlier_conversation(transcript))
                after_change()

    async def events(self):
        while True:
            voice = self.current
            async for event in voice.events():
                if voice is not self.current:
                    continue
                if isinstance(event, TaskRequested):
                    self.task_owners[event.task_id] = voice
                yield event
            if voice is self.current:
                return

    async def send_audio(self, pcm):
        await self.current.send_audio(pcm)

    async def deliver(self, task_id, result, final):
        owner = self.task_owners.get(task_id, self.current)
        if owner is not self.current:
            print(f"answer for a retired voice, not spoken: {result}", flush=True)
            return
        await self.current.deliver(task_id, result, final)

    async def close(self):
        await self.current.close()
