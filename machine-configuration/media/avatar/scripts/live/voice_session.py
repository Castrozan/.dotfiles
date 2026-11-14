import asyncio

import live_voice
from live_events import TaskRequested

HOLDER_CHECK_SECONDS = 0.5


class RoomVoice:
    def __init__(self, open_voice, speaking_voice):
        self.open_voice = open_voice
        self.current = open_voice(speaking_voice, False)
        self.name = self.current.name
        self.input_rate = self.current.input_rate
        self.output_rate = self.current.output_rate
        self.task_owners = {}

    @property
    def speaking_voice(self):
        return self.current.speaking_voice

    async def connect(self):
        return await self.current.connect()

    async def change_to(self, speaking_voice):
        replacement = self.open_voice(speaking_voice, True)
        await replacement.connect()
        previous, self.current = self.current, replacement
        await previous.retire()

    async def follow_the_room_holder(self, directory, after_change):
        while True:
            await asyncio.sleep(HOLDER_CHECK_SECONDS)
            wanted = live_voice.holder_voice(directory)
            if wanted and wanted != self.speaking_voice:
                await self.change_to(wanted)
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
