import asyncio

from voice_identity_fixtures import make_call


def test_the_status_says_the_listener_is_in_the_joined_channel(tmp_path):
    async def scenario():
        _module, call, _identity, channel, _connection = make_call(tmp_path)
        await call.join()
        assert call.status()["listener_present"] is True
        del channel.voice_states[42]
        assert call.status()["listener_present"] is False
        assert call.status()["joined"] is True
        await call.leave()

    asyncio.run(scenario())


def test_the_status_of_a_call_never_joined_has_no_listener_present(tmp_path):
    _module, call, *_ = make_call(tmp_path)
    assert call.status()["joined"] is False
    assert call.status()["listener_present"] is False


def test_a_join_without_following_goes_to_the_listener_channel_once(tmp_path):
    async def scenario():
        _module, call, _identity, channel, _connection = make_call(tmp_path)
        await call.join()
        channel.connect.assert_awaited_once()
        assert call.status()["following"] is False
        await call.follow_listener()
        assert call.status()["joined"] is True
        assert call.status()["channel"] == channel.name
        await call.leave()

    asyncio.run(scenario())
