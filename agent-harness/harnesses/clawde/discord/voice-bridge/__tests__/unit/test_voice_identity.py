import itertools
from types import SimpleNamespace
from unittest.mock import Mock

from voice_identity import VoiceIdentityPool
from voice_permissions import channel_refusal, identity_specifications
from voice_identity_fixtures import make_identity, make_call


def test_every_permission_combination_requires_all_three_permissions():
    identity, channel = make_identity("primary")
    member = channel.guild.me
    for view, connect, speak in itertools.product((False, True), repeat=3):
        channel.permissions_for = Mock(
            return_value=SimpleNamespace(
                view_channel=view, connect=connect, speak=speak
            )
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


def test_pool_closes_clients_before_canceling_receive_tasks(tmp_path):
    import asyncio
    from unittest.mock import AsyncMock

    async def scenario():
        identity, channel = make_identity("primary")
        task = asyncio.create_task(asyncio.Event().wait())

        async def close():
            assert task.cancelling() == 0

        identity.client.close = AsyncMock(side_effect=close)
        await VoiceIdentityPool([identity], tmp_path).close([task])
        identity.client.close.assert_awaited_once()
        assert task.cancelled()

    asyncio.run(scenario())


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
        call._membership.guild_id = 2
        with pytest.raises(module.VoiceCallError, match="no_eligible"):
            await call.join()
        channel.connect.assert_not_awaited()
        call._membership.guild_id = 1
        channel.guild.me.voice = SimpleNamespace(
            channel=channel, session_id="foreign-session"
        )
        with pytest.raises(module.VoiceCallError, match="no_eligible"):
            await call.join()
        channel.connect.assert_not_awaited()
        assert identity.lease is None

    asyncio.run(scenario())


def expected_join_refusal(ready, in_guild, listener_present):
    if not ready:
        return "bridge_not_ready"
    if in_guild and not listener_present:
        return "listener_not_in_allowed_voice_channel"
    return "no_eligible_available_bot_for_listener"


def test_every_join_refusal_names_what_is_actually_missing(tmp_path):
    for ready, in_guild, listener_present in itertools.product((False, True), repeat=3):
        identity, channel = make_identity(
            "primary", ready=ready, guild_id=1 if in_guild else 2
        )
        if not listener_present:
            del channel.voice_states[42]
        pool = VoiceIdentityPool([identity], tmp_path)
        assert pool.join_refusal(42, 1) == expected_join_refusal(
            ready, in_guild, listener_present
        )
