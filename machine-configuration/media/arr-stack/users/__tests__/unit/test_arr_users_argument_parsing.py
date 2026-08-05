import sys
from pathlib import Path

import pytest

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import argument_parsing

SUBCOMMANDS_REQUIRING_USERNAME = [
    "create",
    "delete",
    "reset-password",
    "enable",
    "disable",
]


def test_parser_accepts_list_without_username():
    assert (
        argument_parsing.build_argument_parser().parse_args(["list"]).command == "list"
    )


@pytest.mark.parametrize("subcommand", SUBCOMMANDS_REQUIRING_USERNAME)
def test_parser_accepts_username_subcommands(subcommand):
    arguments = argument_parsing.build_argument_parser().parse_args(
        [subcommand, "Bruno"]
    )
    assert arguments.command == subcommand
    assert arguments.username == "Bruno"


def test_parser_requires_a_subcommand():
    with pytest.raises(SystemExit):
        argument_parsing.build_argument_parser().parse_args([])


def test_parser_accepts_create_with_email():
    arguments = argument_parsing.build_argument_parser().parse_args(
        ["create", "Bruno", "--email", "bruno@example.com"]
    )
    assert arguments.email == "bruno@example.com"


def test_parser_accepts_set_email_with_username_and_email():
    arguments = argument_parsing.build_argument_parser().parse_args(
        ["set-email", "Bruno", "bruno@example.com"]
    )
    assert arguments.command == "set-email"
    assert arguments.username == "Bruno"
    assert arguments.email == "bruno@example.com"


def test_parser_accepts_sync_request_routing_without_username():
    assert (
        argument_parsing.build_argument_parser()
        .parse_args(["sync-request-routing"])
        .command
        == "sync-request-routing"
    )
