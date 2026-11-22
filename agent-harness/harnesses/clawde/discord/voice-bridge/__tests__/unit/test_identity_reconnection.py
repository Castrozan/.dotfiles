import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from hypothesis import given
from hypothesis import strategies as strategies

from voice_connection import (
    RETRY_MAXIMUM_SECONDS,
    IdentityConnection,
    IdentityLogin,
    retry_delay,
)
from voice_identity import VoiceIdentity, VoiceIdentityPool


class ClientConnectorDNSError(OSError):
    pass


class LoginFailure(Exception):
    pass


def fake_client(login_failure=None, bot_user_id=7):
    client = Mock(
        user=SimpleNamespace(id=bot_user_id),
        close=AsyncMock(),
        connect=AsyncMock(),
        is_ready=Mock(return_value=False),
    )
    client.login = AsyncMock(side_effect=login_failure)
    return client


def connection_for(identity, clients, sleep, claimed=None):
    login = IdentityLogin(
        {} if claimed is None else claimed,
        Mock(side_effect=clients),
        (LoginFailure,),
        sleep,
    )
    call = SimpleNamespace(
        release_stale_voice_state=AsyncMock(), follow_listener=AsyncMock()
    )
    return IdentityConnection(identity, call, 42, Mock(), login)


def test_an_identity_whose_name_resolution_fails_at_boot_retries_until_it_connects(
    tmp_path,
):
    first = fake_client(ClientConnectorDNSError())
    second = fake_client(ClientConnectorDNSError())
    third = fake_client()
    identity = VoiceIdentity("primary", first, __file__)
    pool = VoiceIdentityPool([identity], tmp_path)
    observed = []

    async def sleep(seconds):
        observed.append((seconds, pool.status(42, 1)[0], pool.join_refusal(42, 1)))

    asyncio.run(connection_for(identity, [second, third], sleep).run())
    assert [seconds for seconds, _status, _refusal in observed] == [1, 2]
    for _seconds, status, refusal in observed:
        assert status["ready"] is False
        assert status["error"] == "identity_retrying_after_ClientConnectorDNSError"
        assert refusal == "bridge_not_ready"
    assert identity.client is third
    assert identity.error is None
    third.connect.assert_awaited_once()
    for client in (first, second, third):
        client.close.assert_awaited_once()


def test_a_rejected_token_is_reported_and_never_retried():
    identity = VoiceIdentity("primary", fake_client(LoginFailure()), __file__)
    sleep = AsyncMock()
    asyncio.run(connection_for(identity, [], sleep).run())
    assert identity.error == "identity_unavailable_LoginFailure"
    sleep.assert_not_awaited()


def test_a_gateway_that_drops_after_login_is_retried_with_a_fresh_client():
    dropped = fake_client()
    dropped.connect.side_effect = TimeoutError()
    replacement = fake_client()
    identity = VoiceIdentity("primary", dropped, __file__)
    sleep = AsyncMock()
    asyncio.run(connection_for(identity, [replacement], sleep).run())
    sleep.assert_awaited_once_with(1)
    replacement.connect.assert_awaited_once()


def test_a_retried_identity_is_not_its_own_duplicate_but_a_second_grant_is():
    claimed = {}
    identity = VoiceIdentity(
        "primary", fake_client(ClientConnectorDNSError()), __file__
    )
    asyncio.run(connection_for(identity, [fake_client()], AsyncMock(), claimed).run())
    assert identity.error is None
    duplicate = VoiceIdentity("second", fake_client(), __file__)
    asyncio.run(connection_for(duplicate, [], AsyncMock(), claimed).run())
    assert duplicate.error == "duplicate_bot_identity"
    duplicate.client.connect.assert_not_awaited()


def test_ready_resets_the_backoff_then_clears_stale_voice_before_following():
    identity = VoiceIdentity("primary", fake_client(), __file__)
    connection = connection_for(identity, [], AsyncMock())
    order = []
    connection.call.release_stale_voice_state.side_effect = lambda _: order.append(
        "release"
    )
    connection.call.follow_listener.side_effect = lambda: order.append("follow")
    connection.consecutive_failures = 5
    asyncio.run(connection.on_ready())
    assert connection.consecutive_failures == 0
    assert order == ["release", "follow"]
    connection.call.release_stale_voice_state.assert_awaited_once_with(identity)


@given(strategies.integers(min_value=0, max_value=10**9))
def test_every_retry_waits_between_one_second_and_the_maximum(failures):
    assert 1 <= retry_delay(failures) <= RETRY_MAXIMUM_SECONDS


@given(strategies.integers(min_value=0, max_value=10**9))
def test_retries_never_wait_less_after_more_failures(failures):
    assert retry_delay(failures) <= retry_delay(failures + 1)


@given(strategies.integers(min_value=6, max_value=10**9))
def test_persistent_failures_settle_at_the_maximum_wait(failures):
    assert retry_delay(failures) == RETRY_MAXIMUM_SECONDS
