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
    subcommands = set(SUBCOMMANDS_REQUIRING_USERNAME) | {"list"}
    assert set(cli.COMMAND_HANDLERS) == subcommands


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


def test_run_create_reports_import_pending_when_jellyseerr_absent(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.user_account_operations,
        "create_friend_account",
        lambda context, username, password: {
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
