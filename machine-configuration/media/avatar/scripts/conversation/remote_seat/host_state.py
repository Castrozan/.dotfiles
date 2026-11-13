import asyncio
import contextlib
import subprocess

import listener_runtime
import user_units

MEETING_TARGET = "avatar.target"
REFRESH_SECONDS = 2
READ_TIMEOUT_SECONDS = 45
UNKNOWN = {"listening": False, "meeting": False}


def read():
    return {
        "listening": listener_runtime.listening(),
        "meeting": user_units.unit_active(MEETING_TARGET),
    }


class HostState:
    def __init__(self, read_state=read):
        self.read_state = read_state
        self.known = dict(UNKNOWN)

    def snapshot(self):
        return dict(self.known)

    async def refresh(self):
        with contextlib.suppress(OSError, subprocess.SubprocessError, TimeoutError):
            self.known = await asyncio.wait_for(
                asyncio.to_thread(self.read_state), READ_TIMEOUT_SECONDS
            )

    async def follow(self):
        while True:
            await self.refresh()
            await asyncio.sleep(REFRESH_SECONDS)
