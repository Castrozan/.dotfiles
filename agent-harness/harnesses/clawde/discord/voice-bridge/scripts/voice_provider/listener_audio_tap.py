import threading

from voice_provider.pcm_conversion import capture_pcm_from_discord_pcm

CAPTURE_SAMPLE_RATE = 16000
CAPTURE_FRAME_SECONDS = 0.02
CAPTURE_FRAME_BYTES = int(CAPTURE_SAMPLE_RATE * CAPTURE_FRAME_SECONDS) * 2
MAXIMUM_BACKLOG_FRAMES = 25
SILENCE_FRAME = bytes(CAPTURE_FRAME_BYTES)


class ListenerAudioTap:
    def __init__(self):
        self._lock = threading.Lock()
        self._pending = bytearray()

    def append_discord_pcm(self, pcm):
        converted = capture_pcm_from_discord_pcm(pcm)
        with self._lock:
            self._pending.extend(converted)
            excess = len(self._pending) - MAXIMUM_BACKLOG_FRAMES * CAPTURE_FRAME_BYTES
            if excess > 0:
                del self._pending[:excess]

    def take_frame(self):
        with self._lock:
            if len(self._pending) < CAPTURE_FRAME_BYTES:
                return SILENCE_FRAME
            frame = bytes(self._pending[:CAPTURE_FRAME_BYTES])
            del self._pending[:CAPTURE_FRAME_BYTES]
            return frame

    def clear(self):
        with self._lock:
            self._pending.clear()
