import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from media_speech.contract import SpeechRequest, SynthesizedSpeech


class RecordingProvider:
    name = "local-test"
    model = "fixture"
    requires_payment = False

    def __init__(self, speech=None, error=None):
        self.calls = 0
        self.speech = speech or SynthesizedSpeech(b"\x00\x01" * 24000, 24000)
        self.error = error

    def preflight(self, speech_request):
        pass

    def synthesize(self, speech_request):
        self.calls += 1
        if self.error:
            raise self.error
        return self.speech


@pytest.fixture
def speech_request():
    return SpeechRequest("Olá, Lucas.", "pf_dora", "pt-br")


@pytest.fixture
def operation_id():
    return str(uuid.uuid4())


@pytest.fixture
def provider_factory():
    return RecordingProvider
