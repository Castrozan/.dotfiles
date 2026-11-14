import itertools
from types import SimpleNamespace
from unittest.mock import Mock

from voice_identity import (
    VoiceIdentity,
    VoiceIdentityPool,
    channel_refusal,
    identity_specifications,
)


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


def test_every_permission_combination_requires_all_three_permissions():
    identity, channel = make_identity("primary")
    member = channel.guild.me
    for view, connect, speak in itertools.product((False, True), repeat=3):
        channel.permissions_for = lambda member: SimpleNamespace(
            view_channel=view, connect=connect, speak=speak
        )
        assert (channel_refusal(channel, member) is None) is (
            view and connect and speak
        )
    assert identity.lease is None


def test_deterministic_eligible_available_selection_and_preference(tmp_path):
    identities = [make_identity(name)[0] for name in ("z", "a", "m")]
    pool = VoiceIdentityPool(identities, tmp_path)
    assert [identity.name for identity, _ in pool.candidates(42, 1)] == ["a", "m", "z"]
    assert [identity.name for identity, _ in pool.candidates(42, 1, "z")] == [
        "z",
        "a",
        "m",
    ]
    identities[2].preferred_agent = "peer"
    assert next(pool.candidates(42, 1, "peer"))[0].name == "m"
    assert not list(pool.candidates(42, 2))
    assert not list(pool.candidates(99, 1))


def test_failed_offline_busy_and_denied_identities_are_not_candidates(tmp_path):
    identities = [
        make_identity("busy", occupied=True)[0],
        make_identity("offline", ready=False)[0],
        make_identity("denied", allowed=False)[0],
        make_identity("failed")[0],
        make_identity("available")[0],
    ]
    identities[3].error = "login_failed"
    pool = VoiceIdentityPool(identities, tmp_path)
    assert [identity.name for identity, _ in pool.candidates(42, 1)] == ["available"]


def test_unavailable_reasons_match_actual_selection_rules(tmp_path):
    identity, channel = make_identity("primary", allowed=False)
    pool = VoiceIdentityPool([identity], tmp_path)
    assert pool.status(42, 1)[0]["unavailable_reason"] == "missing_voice_permissions"
    assert pool.status(42, 2)[0]["unavailable_reason"] == "bot_not_in_allowed_guild"
    assert (
        pool.status(99, 1)[0]["unavailable_reason"]
        == "listener_not_in_allowed_voice_channel"
    )
    identity.client.is_ready.return_value = False
    assert pool.status(42, 1)[0]["unavailable_reason"] == "identity_not_ready"


def test_local_lease_is_by_bot_user_id_and_released_after_use(tmp_path):
    first = make_identity("first")[0]
    second = make_identity("other")[0]
    pool = VoiceIdentityPool([first, second], tmp_path)
    assert pool.reserve(first)
    assert not pool.reserve(second)
    pool.release(first)
    assert pool.reserve(second)
    pool.release(second)


def test_stage_full_muted_and_deafened_channels_are_refused():
    identity, channel = make_identity("primary")
    member = channel.guild.me
    for attribute in ("mute", "deaf"):
        member.voice = SimpleNamespace(channel=None, mute=False, deaf=False)
        setattr(member.voice, attribute, True)
        assert channel_refusal(channel, member) == "bot_server_muted_or_deafened"
    member.voice = None
    channel.user_limit = 1
    assert channel_refusal(channel, member) == "voice_channel_full"
    channel.user_limit = 0
    channel.type = "stage_voice"
    assert channel_refusal(channel, member) == "unsupported_voice_channel"
    assert identity.lease is None


def test_identity_grants_are_bound_to_host_listener_and_guild():
    grant = {
        "name": "first",
        "tokenFile": "unused",
        "ownerHost": "owner",
        "listenerUserId": "42",
        "guildId": "1",
    }
    assert identity_specifications([grant], "owner", 42, 1) == [grant]
    assert identity_specifications([grant, grant], "owner", 42, 1) == [grant]
    for host, listener, guild in (("other", 42, 1), ("owner", 99, 1), ("owner", 42, 2)):
        assert identity_specifications([grant], host, listener, guild) == []


def load_call_module():
    import importlib.util
    import sys
    from pathlib import Path
    from unittest.mock import patch

    path = Path(__file__).resolve().parents[2] / "scripts/voice_bridge/voice_call.py"
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
    services = module.CallAudioServices(
        "ffmpeg", SpeechSelection([], "voice"), lambda audio: "test"
    )
    call = module.VoiceCall(
        VoiceIdentityPool([identity], tmp_path), 42, 1, services, TranscriptFeed()
    )
    return module, call, identity, channel, connection


def test_join_is_serialized_and_leave_disables_following(tmp_path):
    import asyncio

    async def scenario():
        module, call, identity, channel, connection = make_call(tmp_path)
        results = await asyncio.gather(call.join(follow=True), call.join(follow=True))
        assert all(result["joined"] for result in results)
        channel.connect.assert_awaited_once()
        generation = call.status()["generation"]
        await call.leave()
        assert call.status()["generation"] != generation
        assert call.status()["following"] is False
        await call.follow_listener()
        assert not call.status()["joined"]
        assert identity.lease is None
        connection.stop.assert_called()

    asyncio.run(scenario())


def test_unauthorized_guild_and_occupied_bot_never_connect(tmp_path):
    import asyncio
    import pytest

    async def scenario():
        module, call, identity, channel, connection = make_call(tmp_path)
        call._answered_guild_id = 2
        with pytest.raises(module.VoiceCallError, match="no_eligible"):
            await call.join()
        channel.connect.assert_not_awaited()
        call._answered_guild_id = 1
        channel.guild.me.voice = SimpleNamespace(channel=channel)
        with pytest.raises(module.VoiceCallError, match="no_eligible"):
            await call.join()
        channel.connect.assert_not_awaited()
        assert identity.lease is None

    asyncio.run(scenario())


def test_pending_synthesis_cannot_play_into_a_replacement_call(tmp_path):
    import asyncio
    import contextlib
    from unittest.mock import AsyncMock
    import pytest

    async def scenario():
        module, call, identity, channel, connection = make_call(tmp_path)
        started = asyncio.Event()
        release = asyncio.Event()

        @contextlib.asynccontextmanager
        async def stream(text, language):
            started.set()
            await release.wait()
            yield Mock()

        call._audio_services.synthesizer.streamed_audio = stream
        call._play = AsyncMock()
        await call.join()
        generation = call.status()["generation"]
        speaking = asyncio.create_task(call.speak("old answer", "en-us", generation))
        await started.wait()
        await call.leave()
        await call.join()
        release.set()
        with pytest.raises(module.VoiceCallError, match="stale_call_generation"):
            await speaking
        call._play.assert_not_awaited()
        await call.leave()

    asyncio.run(scenario())
