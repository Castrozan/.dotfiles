import asyncio
import tempfile

from hypothesis import given, settings
from hypothesis import strategies as strategies

from discord_voice_fakes import bridge_process, server_with_listener


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
