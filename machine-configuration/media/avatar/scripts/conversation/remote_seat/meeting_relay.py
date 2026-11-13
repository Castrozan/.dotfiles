import asyncio

MEETING_PATH = "/meeting"
MEETING_SINK = "AvatarRemoteMeeting"
MEETING_RATE = 16000
CLIENT_NAME = "avatar-remote-seat"
MEETING_TAKEN_CODE = 1013


def meeting_playback_command():
    return [
        "pacat",
        "--playback",
        f"--device={MEETING_SINK}",
        f"--client-name={CLIENT_NAME}",
        "--raw",
        "--format=s16le",
        f"--rate={MEETING_RATE}",
        "--channels=1",
        "--latency-msec=60",
    ]


class MeetingRelay:
    def __init__(self, end_process):
        self.end_process = end_process
        self.carrying = False

    async def carry(self, websocket):
        if self.carrying:
            await websocket.close(MEETING_TAKEN_CODE, "Another page carries the call")
            return
        self.carrying = True
        try:
            playback = await asyncio.create_subprocess_exec(
                *meeting_playback_command(), stdin=asyncio.subprocess.PIPE
            )
            try:
                await self.play_frames(websocket, playback.stdin)
            finally:
                await self.end_process(playback)
        finally:
            self.carrying = False

    async def play_frames(self, websocket, playback_input):
        async for frame in websocket:
            if isinstance(frame, bytes):
                playback_input.write(frame)
                await playback_input.drain()
