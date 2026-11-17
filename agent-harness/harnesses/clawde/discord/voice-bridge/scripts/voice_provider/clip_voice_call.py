import io

from voice_bridge.voice_call import VoiceCall, VoiceCallError


class ClipVoiceCall(VoiceCall):
    def __init__(self, *arguments):
        super().__init__(*arguments)
        self._hush_count = 0

    async def play_clip(self, pcm, sample_rate):
        if self._membership.channel() is None:
            raise VoiceCallError("not_in_voice_channel")
        hush_count = self._hush_count
        async with self._speech_lock:
            if hush_count != self._hush_count:
                return {"outcome": "interrupted"}
            outcome = await self._play(io.BytesIO(pcm), sample_rate)
            return {"outcome": outcome}

    def hush(self):
        self._hush_count += 1
        self._interrupted = True
        voice_client = self._membership.voice_client
        if voice_client is not None:
            voice_client.stop()
        return {"outcome": "hushed"}
