import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def authentication(twitter_modules, monkeypatch, tmp_path):
    module = twitter_modules.authentication
    cookies = tmp_path / "cookies" / "cookies.json"
    monkeypatch.setattr(module, "COOKIES_PATH", cookies)
    for name in ("USERNAME_FILE", "EMAIL_FILE", "PASSWORD_FILE"):
        monkeypatch.setattr(module, name, str(tmp_path / name))
    client = SimpleNamespace(
        login=AsyncMock(),
        load_cookies=Mock(),
        user_id=AsyncMock(return_value="user-1"),
        save_cookies=Mock(side_effect=lambda path: cookies.write_text("{}")),
    )
    factory = Mock(return_value=client)
    monkeypatch.setitem(sys.modules, "twikit", SimpleNamespace(Client=factory))
    return module, client, cookies, tmp_path


def test_client_uses_cookies_without_reading_credentials(authentication):
    module, client, cookies, _ = authentication
    cookies.parent.mkdir()
    cookies.write_text("{}")
    assert asyncio.run(module.get_client()) is client
    client.load_cookies.assert_called_once_with(str(cookies))
    client.login.assert_not_awaited()


def test_missing_credentials_fail_without_network(authentication, capsys):
    module, client, _, _ = authentication
    authentication_request = module.get_client()
    with pytest.raises(SystemExit) as failure:
        asyncio.run(authentication_request)
    assert failure.value.code == 1
    assert "No cookies and no credentials" in capsys.readouterr().err
    client.login.assert_not_awaited()


def test_client_reads_secret_files_and_protects_saved_cookies(authentication):
    module, client, cookies, directory = authentication
    for name, value in [
        ("USERNAME_FILE", "reader"),
        ("EMAIL_FILE", "reader@example.test"),
        ("PASSWORD_FILE", "test-password"),
    ]:
        (directory / name).write_text(value + "\n")
    assert asyncio.run(module.get_client()) is client
    client.login.assert_awaited_once_with(
        auth_info_1="reader",
        auth_info_2="reader@example.test",
        password="test-password",
    )
    assert cookies.stat().st_mode & 0o777 == 0o600


def test_login_reuses_valid_session_and_refreshes_expired_session(
    authentication, monkeypatch, capsys
):
    module, client, cookies, _ = authentication
    cookies.parent.mkdir()
    cookies.write_text("{}")
    asyncio.run(module.command_login(SimpleNamespace(totp=None)))
    assert "Already authenticated as user user-1" in capsys.readouterr().out
    client.login.assert_not_awaited()
    client.user_id.side_effect = RuntimeError("expired")
    answers = iter(["reader", "reader@example.test", "test-password"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    asyncio.run(module.command_login(SimpleNamespace(totp="test-totp")))
    client.login.assert_awaited_once_with(
        auth_info_1="reader",
        auth_info_2="reader@example.test",
        password="test-password",
        totp_secret="test-totp",
    )
    assert cookies.stat().st_mode & 0o777 == 0o600
    output = capsys.readouterr().out
    assert "expired" in output
    assert "test-password" not in output


def test_secret_reader_tolerates_missing_path(twitter_modules, tmp_path):
    assert twitter_modules.serializers.read_secret_file("") is None
    assert twitter_modules.serializers.read_secret_file(tmp_path / "missing") is None
