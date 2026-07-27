import importlib.util
import sys
from pathlib import Path

import pytest

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))


def load_cli_module():
    module_specification = importlib.util.spec_from_file_location(
        "arr_users_cli_sync", ARR_USERS_PACKAGE_DIRECTORY_PATH / "__main__.py"
    )
    module = importlib.util.module_from_spec(module_specification)
    module_specification.loader.exec_module(module)
    return module


cli = load_cli_module()


def test_parser_accepts_sync_without_username():
    assert (
        cli.argument_parsing.build_argument_parser().parse_args(["sync"]).command
        == "sync"
    )


def test_sync_builds_a_jellyfin_only_context(monkeypatch):
    monkeypatch.setattr(
        cli.runtime_credentials, "jellyfin_base_url", lambda: "http://jellyfin"
    )
    monkeypatch.setattr(cli.runtime_credentials, "read_jellyfin_api_key", lambda: "key")

    def fail_on_jellyseerr_read():
        raise AssertionError("sync must not require the Jellyseerr settings file")

    monkeypatch.setattr(
        cli.runtime_credentials, "read_jellyseerr_api_key", fail_on_jellyseerr_read
    )
    context = cli.build_context_for_command("sync")

    assert context.jellyfin_api_key == "key"
    assert context.jellyseerr_api_key == ""


def test_non_sync_commands_still_build_the_full_context(monkeypatch):
    monkeypatch.setattr(
        cli.runtime_credentials, "jellyfin_base_url", lambda: "http://jellyfin"
    )
    monkeypatch.setattr(cli.runtime_credentials, "read_jellyfin_api_key", lambda: "key")
    monkeypatch.setattr(
        cli.runtime_credentials, "jellyseerr_base_url", lambda: "http://jellyseerr"
    )
    monkeypatch.setattr(
        cli.runtime_credentials, "read_jellyseerr_api_key", lambda: "seerr-key"
    )
    context = cli.build_context_for_command("list")

    assert context.jellyseerr_api_key == "seerr-key"


def test_run_sync_names_the_libraries_friends_cannot_see(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.library_access_synchronization,
        "synchronize_library_access",
        lambda context: {
            "created_libraries": ["Movies (Private)"],
            "failed_libraries": [],
            "public_libraries": ["Movies", "TV"],
            "private_libraries": ["Movies (Private)"],
            "reconciled_accounts": ["Rogerio"],
        },
    )
    cli.run_sync(
        object(), cli.argument_parsing.build_argument_parser().parse_args(["sync"])
    )

    printed = capsys.readouterr().out
    assert "friends can see: Movies, TV" in printed
    assert "friends cannot see: Movies (Private)" in printed
    assert "reconciled: Rogerio" in printed


def test_run_sync_reports_the_reconcile_before_failing_on_a_library(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        cli.library_access_synchronization,
        "synchronize_library_access",
        lambda context: {
            "created_libraries": [],
            "failed_libraries": ["Movies (Private)"],
            "public_libraries": ["Movies", "TV"],
            "private_libraries": [],
            "reconciled_accounts": ["Rogerio"],
        },
    )

    with pytest.raises(ValueError, match="Movies \\(Private\\)"):
        cli.run_sync(
            object(), cli.argument_parsing.build_argument_parser().parse_args(["sync"])
        )

    assert "reconciled: Rogerio" in capsys.readouterr().out


def test_run_sync_request_routing_names_the_account_it_routes(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.request_routing_synchronization,
        "synchronize_request_routing",
        lambda context: {
            "routed_account": "private-requests",
            "created_rules": ["movies to /data/media/movies-private"],
            "updated_rules": [],
            "removed_rules": [],
        },
    )
    cli.run_sync_request_routing(
        object(),
        cli.argument_parsing.build_argument_parser().parse_args(
            ["sync-request-routing"]
        ),
    )

    printed = capsys.readouterr().out
    assert "routing every request from: private-requests" in printed
    assert "created rules: movies to /data/media/movies-private" in printed
    assert "removed rules: none" in printed


def test_run_sync_request_routing_says_nothing_routes_without_the_account(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        cli.request_routing_synchronization,
        "synchronize_request_routing",
        lambda context: {
            "routed_account": None,
            "created_rules": [],
            "updated_rules": [],
            "removed_rules": [],
        },
    )
    cli.run_sync_request_routing(
        object(),
        cli.argument_parsing.build_argument_parser().parse_args(
            ["sync-request-routing"]
        ),
    )

    assert "no request routes privately yet" in capsys.readouterr().out


def test_run_sync_reports_none_when_nothing_was_created(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.library_access_synchronization,
        "synchronize_library_access",
        lambda context: {
            "created_libraries": [],
            "failed_libraries": [],
            "public_libraries": ["Movies", "TV"],
            "private_libraries": [],
            "reconciled_accounts": [],
        },
    )
    cli.run_sync(
        object(), cli.argument_parsing.build_argument_parser().parse_args(["sync"])
    )

    printed = capsys.readouterr().out
    assert "created libraries: none" in printed
    assert "reconciled: none" in printed
