import asyncio
import logging
from collections.abc import AsyncIterator

import numpy as np
import sounddevice as sd
import janus

logger = logging.getLogger(__name__)


class SounddeviceCapture:
    def __init__(
        self,
        device: str | int | None = None,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
    ) -> None:
        self._device = device
        self._sample_rate = sample_rate
        self._frame_duration_ms = frame_duration_ms
        self._frame_size = int(sample_rate * frame_duration_ms / 1000)
        self._stream: sd.InputStream | None = None
        self._queue: janus.Queue[bytes] | None = None

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def frame_size(self) -> int:
        return self._frame_size

    async def start(self) -> None:
        self._queue = janus.Queue(maxsize=100)

        def audio_callback(indata: np.ndarray, frames: int, time_info, status) -> None:
            if status:
                logger.warning("Audio capture status: %s", status)
            pcm_bytes = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            try:
                self._queue.sync_q.put_nowait(pcm_bytes)
            except janus.SyncQueueFull:
                pass

        device = self._resolve_device()
        self._stream = sd.InputStream(
            device=device,
            samplerate=self._sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self._frame_size,
            callback=audio_callback,
        )
        self._stream.start()
        logger.info(
            "Audio capture started (device=%s, rate=%d, frame=%dms)",
            device, self._sample_rate, self._frame_duration_ms,
        )

    async def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._queue:
            self._queue.close()
            await self._queue.async_q.join()
            self._queue = None

    async def read_frames(self) -> AsyncIterator[bytes]:
        if not self._queue:
            return
        while True:
            try:
                frame = await asyncio.wait_for(
                    self._queue.async_q.get(), timeout=1.0
                )
                yield frame
            except asyncio.TimeoutError:
                continue
            except janus.AsyncQueueShutDown:
                break

    def _resolve_device(self) -> str | int | None:
        if self._device is None:
            return None
        if isinstance(self._device, int):
            return self._device
        try:
            return int(self._device)
        except ValueError:
            pass
        for i, dev in enumerate(sd.query_devices()):
            if self._device.lower() in dev["name"].lower() and dev["max_input_channels"] > 0:
                logger.info("Resolved device '%s' -> %d (%s)", self._device, i, dev["name"])
                return i
        logger.warning("Device '%s' not found, using default", self._device)
        return None


class SounddevicePlayback:
    def __init__(self, sample_rate: int = 24000) -> None:
        self._sample_rate = sample_rate
        self._stream: sd.OutputStream | None = None
        self._queue: janus.Queue[bytes | None] | None = None
        self._play_task: asyncio.Task | None = None
        self._cancelled = False

    async def start(self) -> None:
        self._queue = janus.Queue(maxsize=200)
        self._cancelled = False

        self._stream = sd.OutputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype="int16",
        )
        self._stream.start()
        self._play_task = asyncio.create_task(self._playback_loop())

    async def stop(self) -> None:
        if self._queue:
            await self._queue.async_q.put(None)
        if self._play_task:
            await self._play_task
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._queue:
            self._queue.close()
            self._queue = None

    async def play_chunk(self, audio_data: bytes) -> None:
        if self._queue and not self._cancelled:
            await self._queue.async_q.put(audio_data)

    async def drain(self) -> None:
        if self._queue:
            await self._queue.async_q.put(b"__DRAIN__")
            while not self._queue.async_q.empty():
                await asyncio.sleep(0.01)

    async def cancel(self) -> None:
        self._cancelled = True
        if self._queue:
            while not self._queue.sync_q.empty():
                try:
                    self._queue.sync_q.get_nowait()
                except Exception:
                    break
        if self._stream:
            self._stream.stop()
            self._stream.start()
        self._cancelled = False

    async def _playback_loop(self) -> None:
        while True:
            if not self._queue:
                break
            try:
                chunk = await self._queue.async_q.get()
            except janus.AsyncQueueShutDown:
                break

            if chunk is None:
                break
            if chunk == b"__DRAIN__":
                continue
            if self._cancelled:
                continue
            if self._stream:
                audio_array = np.frombuffer(chunk, dtype=np.int16)
                try:
                    self._stream.write(audio_array.reshape(-1, 1))
                except sd.PortAudioError:
                    logger.warning("Playback write error")
