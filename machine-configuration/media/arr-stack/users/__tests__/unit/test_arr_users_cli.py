import importlib.util
import io
import sys
import urllib.error
from pathlib import Path

import pytest

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))


def load_cli_module():
    module_specification = importlib.util.spec_from_file_location(
        "arr_users_cli", ARR_USERS_PACKAGE_DIRECTORY_PATH / "__main__.py"
    )
    module = importlib.util.module_from_spec(module_specification)
    module_specification.loader.exec_module(module)
    return module


cli = load_cli_module()


def test_every_subcommand_has_a_handler():
    assert set(cli.command_handlers.COMMAND_HANDLERS) == {
        "create",
        "delete",
        "reset-password",
        "enable",
        "disable",
        "list",
        "set-email",
        "sync",
        "sync-kavita-access",
        "sync-request-routing",
        "sync-account-permissions",
    }


def test_run_set_email_prints_username_and_email(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.command_handlers.user_account_operations,
        "set_friend_email",
        lambda context, username, email: {"username": username, "email": email},
    )
    arguments = cli.argument_parsing.build_argument_parser().parse_args(
        ["set-email", "Bruno", "bruno@example.com"]
    )
    cli.command_handlers.run_set_email(object(), arguments)

    printed = capsys.readouterr().out
    assert "Bruno" in printed
    assert "bruno@example.com" in printed


def test_main_maps_value_error_to_exit_one(monkeypatch):
    monkeypatch.setattr(cli.command_contexts, "build_context", lambda: object())

    def raise_value_error(context):
        raise ValueError("no such user")

    monkeypatch.setattr(cli.command_handlers.user_account_operations, "list_accounts", raise_value_error)
    monkeypatch.setattr(sys, "argv", ["arr-users", "list"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1


def test_main_maps_http_error_to_exit_one(monkeypatch):
    monkeypatch.setattr(cli.command_contexts, "build_context", lambda: object())

    def raise_http_error(context):
        raise urllib.error.HTTPError(
            "http://jellyfin/Users", 500, "boom", {}, io.BytesIO(b"body")
        )

    monkeypatch.setattr(cli.command_handlers.user_account_operations, "list_accounts", raise_http_error)
    monkeypatch.setattr(sys, "argv", ["arr-users", "list"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1


def test_main_maps_url_error_to_exit_one(monkeypatch):
    monkeypatch.setattr(cli.command_contexts, "build_context", lambda: object())

    def raise_url_error(context):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(cli.command_handlers.user_account_operations, "list_accounts", raise_url_error)
    monkeypatch.setattr(sys, "argv", ["arr-users", "list"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1


def test_run_create_prints_email_when_set_and_import_succeeded(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.command_handlers.user_account_operations,
        "create_friend_account",
        lambda context, username, password, email: {
            "username": username,
            "password": "generated-pw",
            "jellyfin_user_id": "id",
            "jellyseerr_user_id": 9,
        },
    )
    arguments = cli.argument_parsing.build_argument_parser().parse_args(
        ["create", "Bruno", "--email", "bruno@example.com"]
    )
    cli.command_handlers.run_create(object(), arguments)

    assert "email: bruno@example.com" in capsys.readouterr().out


def test_run_create_omits_email_line_when_import_pending(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.command_handlers.user_account_operations,
        "create_friend_account",
        lambda context, username, password, email: {
            "username": username,
            "password": "generated-pw",
            "jellyfin_user_id": "id",
            "jellyseerr_user_id": None,
        },
    )
    arguments = cli.argument_parsing.build_argument_parser().parse_args(
        ["create", "Bruno", "--email", "bruno@example.com"]
    )
    cli.command_handlers.run_create(object(), arguments)

    printed = capsys.readouterr().out
    assert "email:" not in printed
    assert "import pending" in printed


def test_run_create_reports_import_pending_when_jellyseerr_absent(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.command_handlers.user_account_operations,
        "create_friend_account",
        lambda context, username, password, email: {
            "username": username,
            "password": "generated-pw",
            "jellyfin_user_id": "id",
            "jellyseerr_user_id": None,
        },
    )
    arguments = cli.argument_parsing.build_argument_parser().parse_args(
        ["create", "Bruno"]
    )
    cli.command_handlers.run_create(object(), arguments)

    printed = capsys.readouterr().out
    assert "Bruno" in printed
    assert "generated-pw" in printed
    assert "import pending" in printed
