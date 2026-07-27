import importlib.util
import sys
from pathlib import Path

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))


def load_cli_module():
    module_specification = importlib.util.spec_from_file_location(
        "arr_users_cli_account_permissions",
        ARR_USERS_PACKAGE_DIRECTORY_PATH / "__main__.py",
    )
    module = importlib.util.module_from_spec(module_specification)
    module_specification.loader.exec_module(module)
    return module


cli = load_cli_module()


def parse_sync_account_permissions():
    return cli.argument_parsing.build_argument_parser().parse_args(
        ["sync-account-permissions"]
    )


def test_the_permission_reconcile_needs_the_jellyseerr_context():
    assert "sync-account-permissions" not in cli.JELLYFIN_ONLY_COMMANDS


def test_run_sync_account_permissions_names_who_can_still_approve(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.account_permission_synchronization,
        "synchronize_account_permissions",
        lambda context: {
            "administrator_accounts": ["jellyseerr"],
            "self_approving_accounts": ["lucas", "Rogerio"],
            "rewritten_accounts": ["lucas"],
        },
    )
    cli.run_sync_account_permissions(object(), parse_sync_account_permissions())

    printed = capsys.readouterr().out
    assert "administered by: jellyseerr" in printed
    assert "requesting without approval: lucas, Rogerio" in printed
    assert "rewritten: lucas" in printed


def test_run_sync_account_permissions_reports_an_untouched_jellyseerr(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        cli.account_permission_synchronization,
        "synchronize_account_permissions",
        lambda context: {
            "administrator_accounts": ["jellyseerr"],
            "self_approving_accounts": ["Rogerio"],
            "rewritten_accounts": [],
        },
    )
    cli.run_sync_account_permissions(object(), parse_sync_account_permissions())

    assert "rewritten: none" in capsys.readouterr().out
