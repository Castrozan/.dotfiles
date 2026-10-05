import time

from media_video.contract import VideoError


class ExecutionDeadline:
    def __init__(self, seconds):
        self.started_at = time.monotonic()
        self.expires_at = self.started_at + seconds

    def remaining(self):
        remaining = self.expires_at - time.monotonic()
        if remaining <= 0:
            raise VideoError("deadline_exceeded")
        return remaining

    def elapsed(self):
        return time.monotonic() - self.started_at
