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

SUBCOMMANDS_REQUIRING_USERNAME = [
    "create",
    "delete",
    "reset-password",
    "enable",
    "disable",
]


def test_parser_accepts_list_without_username():
    assert cli.build_argument_parser().parse_args(["list"]).command == "list"


@pytest.mark.parametrize("subcommand", SUBCOMMANDS_REQUIRING_USERNAME)
def test_parser_accepts_username_subcommands(subcommand):
    arguments = cli.build_argument_parser().parse_args([subcommand, "Bruno"])
    assert arguments.command == subcommand
    assert arguments.username == "Bruno"


def test_parser_requires_a_subcommand():
    with pytest.raises(SystemExit):
        cli.build_argument_parser().parse_args([])


def test_every_subcommand_has_a_handler():
    subcommands = set(SUBCOMMANDS_REQUIRING_USERNAME) | {"list", "set-email"}
    assert set(cli.COMMAND_HANDLERS) == subcommands


def test_parser_accepts_create_with_email():
    arguments = cli.build_argument_parser().parse_args(
        ["create", "Bruno", "--email", "bruno@example.com"]
    )
    assert arguments.email == "bruno@example.com"


def test_parser_accepts_set_email_with_username_and_email():
    arguments = cli.build_argument_parser().parse_args(
        ["set-email", "Bruno", "bruno@example.com"]
    )
    assert arguments.command == "set-email"
    assert arguments.username == "Bruno"
    assert arguments.email == "bruno@example.com"


def test_run_set_email_prints_username_and_email(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.user_account_operations,
        "set_friend_email",
        lambda context, username, email: {"username": username, "email": email},
    )
    arguments = cli.build_argument_parser().parse_args(
        ["set-email", "Bruno", "bruno@example.com"]
    )
    cli.run_set_email(object(), arguments)

    printed = capsys.readouterr().out
    assert "Bruno" in printed
    assert "bruno@example.com" in printed


def test_main_maps_value_error_to_exit_one(monkeypatch):
    monkeypatch.setattr(cli, "build_context", lambda: object())

    def raise_value_error(context):
        raise ValueError("no such user")

    monkeypatch.setattr(cli.user_account_operations, "list_accounts", raise_value_error)
    monkeypatch.setattr(sys, "argv", ["arr-users", "list"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1


def test_main_maps_http_error_to_exit_one(monkeypatch):
    monkeypatch.setattr(cli, "build_context", lambda: object())

    def raise_http_error(context):
        raise urllib.error.HTTPError(
            "http://jellyfin/Users", 500, "boom", {}, io.BytesIO(b"body")
        )

    monkeypatch.setattr(cli.user_account_operations, "list_accounts", raise_http_error)
    monkeypatch.setattr(sys, "argv", ["arr-users", "list"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1


def test_main_maps_url_error_to_exit_one(monkeypatch):
    monkeypatch.setattr(cli, "build_context", lambda: object())

    def raise_url_error(context):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(cli.user_account_operations, "list_accounts", raise_url_error)
    monkeypatch.setattr(sys, "argv", ["arr-users", "list"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == 1


def test_run_create_prints_email_when_set_and_import_succeeded(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.user_account_operations,
        "create_friend_account",
        lambda context, username, password, email: {
            "username": username,
            "password": "generated-pw",
            "jellyfin_user_id": "id",
            "jellyseerr_user_id": 9,
        },
    )
    arguments = cli.build_argument_parser().parse_args(
        ["create", "Bruno", "--email", "bruno@example.com"]
    )
    cli.run_create(object(), arguments)

    assert "email: bruno@example.com" in capsys.readouterr().out


def test_run_create_omits_email_line_when_import_pending(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.user_account_operations,
        "create_friend_account",
        lambda context, username, password, email: {
            "username": username,
            "password": "generated-pw",
            "jellyfin_user_id": "id",
            "jellyseerr_user_id": None,
        },
    )
    arguments = cli.build_argument_parser().parse_args(
        ["create", "Bruno", "--email", "bruno@example.com"]
    )
    cli.run_create(object(), arguments)

    printed = capsys.readouterr().out
    assert "email:" not in printed
    assert "import pending" in printed


def test_run_create_reports_import_pending_when_jellyseerr_absent(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.user_account_operations,
        "create_friend_account",
        lambda context, username, password, email: {
            "username": username,
            "password": "generated-pw",
            "jellyfin_user_id": "id",
            "jellyseerr_user_id": None,
        },
    )
    arguments = cli.build_argument_parser().parse_args(["create", "Bruno"])
    cli.run_create(object(), arguments)

    printed = capsys.readouterr().out
    assert "Bruno" in printed
    assert "generated-pw" in printed
    assert "import pending" in printed
