import asyncio
import tempfile
from unittest.mock import Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as strategies

from discord_voice_fakes import (
    BOT_USER_ID,
    bridge_process,
    server_with_listener,
)


def primary_status(bridge):
    return bridge.call.status()["identities"][0]


def test_a_close_after_a_fresh_gateway_session_takes_the_bot_out_of_the_channel(
    tmp_path,
):
    async def scenario():
        server = server_with_listener()
        bridge = bridge_process(server, tmp_path)
        await bridge.call.join()
        bridge.client.fresh_session("second-session")
        await bridge.call.leave()
        assert server.bot_session() is None
        assert bridge.client.guild.me.voice is None
        assert primary_status(bridge)["unavailable_reason"] is None
        await bridge.call.join()
        assert bridge.call.status()["joined"] is True
        await bridge.call.leave()

    asyncio.run(scenario())


def test_a_leave_that_could_not_be_sent_is_cleared_before_the_next_join(tmp_path):
    async def scenario():
        server = server_with_listener()
        bridge = bridge_process(server, tmp_path)
        await bridge.call.join()
        bridge.client.gateway_open = False
        await bridge.call.leave()
        assert server.bot_session() == "first-session"
        bridge.client.gateway_open = True
        await bridge.call.join()
        assert bridge.call.status()["joined"] is True
        assert bridge.client.sent_voice_states[-2:] == [
            None,
            bridge.client.guild.voice_channels[0],
        ]
        await bridge.call.leave()

    asyncio.run(scenario())


def test_a_restarted_bridge_clears_the_voice_state_its_previous_process_left(
    tmp_path,
):
    async def scenario():
        server = server_with_listener()
        first = bridge_process(server, tmp_path)
        await first.call.join()
        first.client.gateway_open = False
        await first.call.leave()
        restarted = bridge_process(server, tmp_path, "restarted-session")
        assert primary_status(restarted)["unavailable_reason"] is None
        await restarted.call.release_stale_voice_state(restarted.identity)
        assert server.bot_session() is None
        await restarted.call.join()
        assert server.bot_session() == "restarted-session"
        await restarted.call.leave()

    asyncio.run(scenario())


def test_a_bot_in_voice_through_another_owner_is_refused_and_left_alone(tmp_path):
    async def scenario():
        server = server_with_listener()
        bridge = bridge_process(server, tmp_path)
        channel = bridge.client.guild.voice_channels[0]
        server.update_voice_state(BOT_USER_ID, "another-owner-session", channel)
        assert primary_status(bridge)["unavailable_reason"] == (
            "bot_voice_connection_in_use"
        )
        await bridge.call.release_stale_voice_state(bridge.identity)
        with pytest.raises(
            bridge.module.VoiceCallError, match="no_eligible_available_bot"
        ):
            await bridge.call.join()
        assert server.bot_session() == "another-owner-session"
        assert bridge.client.sent_voice_states == []

    asyncio.run(scenario())


def test_the_startup_sweep_never_touches_the_call_in_progress(tmp_path):
    async def scenario():
        server = server_with_listener()
        bridge = bridge_process(server, tmp_path)
        await bridge.call.join()
        bridge.client.fresh_session("second-session")
        await bridge.call.release_stale_voice_state(bridge.identity)
        assert server.bot_session() == "first-session"
        assert bridge.call.status()["joined"] is True
        await bridge.call.leave()

    asyncio.run(scenario())


def test_following_never_rejoins_after_the_close(tmp_path):
    async def scenario():
        server = server_with_listener()
        bridge = bridge_process(server, tmp_path)
        await bridge.call.join(follow=True)
        await asyncio.gather(bridge.call.leave(), bridge.call.follow_listener())
        await bridge.call.follow_listener()
        assert server.bot_session() is None
        joins = [state for state in bridge.client.sent_voice_states if state]
        assert len(joins) == 1

    asyncio.run(scenario())


def test_a_listener_outside_any_channel_is_the_reason_given(tmp_path):
    async def scenario():
        server = server_with_listener()
        server.voice_states.clear()
        bridge = bridge_process(server, tmp_path)
        with pytest.raises(
            bridge.module.VoiceCallError,
            match="^listener_not_in_allowed_voice_channel$",
        ):
            await bridge.call.join()

    asyncio.run(scenario())


def test_a_join_whose_session_cannot_be_recorded_leaves_instead_of_hiding(
    tmp_path,
):
    async def scenario():
        server = server_with_listener()
        bridge = bridge_process(server, tmp_path)
        pool = bridge.call._membership.identities
        pool.voice_sessions.remember = Mock(side_effect=OSError("read-only"))
        with pytest.raises(OSError):
            await bridge.call.join()
        assert server.bot_session() is None
        assert bridge.identity.lease is None

    asyncio.run(scenario())


DISRUPTIONS = ("none", "fresh_session", "unsent_leave", "restart")


async def disrupted_cycles(disruptions, lease_directory):
    server = server_with_listener()
    bridge = bridge_process(server, lease_directory)
    for index, disruption in enumerate(disruptions):
        await bridge.call.join()
        assert bridge.call.status()["joined"] is True
        if disruption == "fresh_session":
            bridge.client.fresh_session(f"session-{index}")
        bridge.client.gateway_open = disruption not in ("unsent_leave", "restart")
        await bridge.call.leave()
        bridge.client.gateway_open = True
        if disruption == "restart":
            bridge = bridge_process(server, lease_directory, f"restart-{index}")
    await bridge.call.join()
    await bridge.call.leave()
    return server


@settings(deadline=None, max_examples=60)
@given(strategies.lists(strategies.sampled_from(DISRUPTIONS), max_size=6))
def test_every_close_and_reopen_sequence_reopens_and_ends_out_of_the_channel(
    disruptions,
):
    with tempfile.TemporaryDirectory() as lease_directory:
        server = asyncio.run(disrupted_cycles(disruptions, lease_directory))
    assert server.bot_session() is None
