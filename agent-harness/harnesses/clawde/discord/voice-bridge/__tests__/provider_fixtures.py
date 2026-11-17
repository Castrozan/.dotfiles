import asyncio
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from voice_identity_fixtures import make_call

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name, relative_path, replaced_modules):
    specification = importlib.util.spec_from_file_location(
        name, SCRIPTS / relative_path
    )
    module = importlib.util.module_from_spec(specification)
    with patch.dict(sys.modules, {module.__name__: module, **replaced_modules}):
        specification.loader.exec_module(module)
    return module


class FakePlayback:
    def __init__(self, voice_client):
        self.played = []
        self.started = asyncio.Event()
        self._stopped = asyncio.Event()
        voice_client.stop = Mock(side_effect=self._stopped.set)

    def finish(self):
        self._stopped.set()

    async def play_audio_stream(
        self, _voice_client, audio_stream, sample_rate, _ffmpeg
    ):
        self.played.append((sample_rate, audio_stream.read()))
        self.started.clear()
        self._stopped.clear()
        self.started.set()
        await self._stopped.wait()


def make_clip_call(tmp_path):
    call_module, call, _identity, channel, connection = make_call(tmp_path)
    receiver = SimpleNamespace(
        listener_packet_count=0,
        buffered_listener_seconds=lambda: 0.0,
        check_silence=lambda: [],
        flush_pending=lambda: [],
        sustained_speech_seconds=lambda: 0.0,
        forget_sustained_speech=lambda: None,
        start=lambda: None,
        stop=lambda: None,
    )
    call_module.ListenerVoiceReceiver = Mock(return_value=receiver)
    playback = FakePlayback(connection)
    call_module.play_audio_stream = playback.play_audio_stream
    clip_module = load_module(
        "clip_voice_call_under_test",
        "voice_provider/clip_voice_call.py",
        {"voice_bridge.voice_call": call_module},
    )
    clip_call = clip_module.ClipVoiceCall(
        call._membership.identities, 42, 1, call._audio_services, call._feed
    )
    return call_module, clip_call, playback, connection


def load_control_server(call_module):
    return load_module(
        "control_server_under_test",
        "voice_bridge/control_server.py",
        {"voice_bridge.voice_call": Mock(VoiceCallError=call_module.VoiceCallError)},
    )
