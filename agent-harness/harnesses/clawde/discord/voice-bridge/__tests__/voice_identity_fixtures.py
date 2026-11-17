from types import SimpleNamespace
from unittest.mock import Mock

from voice_identity import VoiceIdentity, VoiceIdentityPool


def make_identity(name, *, ready=True, occupied=False, allowed=True, guild_id=1):
    permissions = SimpleNamespace(view_channel=allowed, connect=allowed, speak=allowed)
    member = SimpleNamespace(voice=None)
    channel = SimpleNamespace(
        id=10,
        name="call",
        type="voice",
        user_limit=0,
        voice_states={42: object()},
        permissions_for=lambda member: permissions,
    )
    guild = SimpleNamespace(
        id=guild_id, name="guild", me=member, voice_channels=[channel]
    )
    channel.guild = guild
    if occupied:
        member.voice = SimpleNamespace(channel=channel, mute=False, deaf=False)
    client = Mock(
        user=SimpleNamespace(id=100 + len(name)),
        is_ready=Mock(return_value=ready),
        get_guild=lambda requested: guild if requested == guild_id else None,
    )
    return VoiceIdentity(name, client, "unused"), channel


def load_call_module():
    import importlib.util
    import sys
    from pathlib import Path
    from unittest.mock import patch

    path = Path(__file__).resolve().parent.parent / "scripts/voice_bridge/voice_call.py"
    specification = importlib.util.spec_from_file_location(
        "voice_call_under_test", path
    )
    module = importlib.util.module_from_spec(specification)
    with patch.dict(
        sys.modules,
        {
            module.__name__: module,
            "voice_bridge.listener_receiver": Mock(),
            "voice_bridge.voice_playback": Mock(),
        },
    ):
        specification.loader.exec_module(module)
    return module


def make_call(tmp_path):
    from unittest.mock import AsyncMock
    from voice_bridge.speech_synthesis import SpeechSelection
    from voice_bridge.transcript_feed import TranscriptFeed

    module = load_call_module()
    identity, channel = make_identity("primary")
    connection = Mock(
        channel=channel, is_connected=Mock(return_value=True), disconnect=AsyncMock()
    )
    channel.connect = AsyncMock(return_value=connection)
    module.ListenerVoiceReceiver = Mock(return_value=Mock(listener_packet_count=0))
    services = SimpleNamespace(
        ffmpeg="ffmpeg",
        synthesizer=SpeechSelection([], "voice"),
        transcribe_audio=lambda audio: "test",
        listener_audio=Mock(),
    )
    call = module.VoiceCall(
        VoiceIdentityPool([identity], tmp_path), 42, 1, services, TranscriptFeed()
    )
    return module, call, identity, channel, connection
