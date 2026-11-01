import asyncio
import contextlib
import json
import shutil
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

SPEECH_MODEL = "eleven_v4"
SPEECH_DELIVERY = "natural and conversational"
SYNTHESIS_TIMEOUT_SECONDS = 15


class SpeechSynthesisError(Exception):
    pass


@dataclass(frozen=True)
class SpeechSynthesizer:
    media_speech_command: str
    voice: str
    scratch_directory: Path

    @contextlib.asynccontextmanager
    async def synthesized_audio(self, text, language) -> AsyncIterator[str]:
        state_directory = tempfile.mkdtemp(dir=self.scratch_directory)
        try:
            yield await self._generate(text, language, state_directory)
        finally:
            shutil.rmtree(state_directory, ignore_errors=True)

    async def _generate(self, text, language, state_directory):
        process = await asyncio.create_subprocess_exec(
            self.media_speech_command,
            "--state-directory",
            state_directory,
            "generate",
            "--provider",
            "elevenlabs",
            "--model",
            SPEECH_MODEL,
            "--directions",
            SPEECH_DELIVERY,
            "--language",
            language,
            "--voice",
            self.voice,
            "--text",
            text,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            output, errors = await asyncio.wait_for(
                process.communicate(), SYNTHESIS_TIMEOUT_SECONDS
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            raise SpeechSynthesisError("synthesis_timed_out") from None
        if process.returncode != 0:
            raise SpeechSynthesisError(errors.decode(errors="replace").strip()[-200:])
        return json.loads(output)["audio"]["path"]
