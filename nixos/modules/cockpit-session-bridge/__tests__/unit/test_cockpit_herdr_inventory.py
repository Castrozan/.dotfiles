import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_herdr_snapshot
import cockpit_multiplexer_port
from cockpit_herdr_test_doubles import (
    DOTFILES_SNAPSHOT_OUTPUT,
    build_runtime_snapshot_output,
)


def test_a_workspace_becomes_a_session_and_its_tabs_become_that_session_windows():
    parsed_sessions = cockpit_herdr_snapshot.parse_herdr_runtime_snapshot(
        DOTFILES_SNAPSHOT_OUTPUT
    )

    assert parsed_sessions == [
        cockpit_multiplexer_port.CockpitMultiplexerSession(
            session_name="dotfiles",
            windows=(
                cockpit_multiplexer_port.CockpitMultiplexerWindow(
                    "w1T:tB", "AIDP", "claude"
                ),
                cockpit_multiplexer_port.CockpitMultiplexerWindow(
                    "w1T:tF", "hooks", ""
                ),
            ),
        ),
        cockpit_multiplexer_port.CockpitMultiplexerSession(
            session_name="clawde",
            windows=(
                cockpit_multiplexer_port.CockpitMultiplexerWindow(
                    "w1P:t3E", "jenny", "codex"
                ),
            ),
        ),
    ]


def test_a_workspace_with_no_tabs_still_lists_as_an_empty_session():
    parsed_sessions = cockpit_herdr_snapshot.parse_herdr_runtime_snapshot(
        build_runtime_snapshot_output(
            workspaces=[{"workspace_id": "wZ", "label": "scratch"}], tabs=[]
        )
    )

    assert parsed_sessions == [
        cockpit_multiplexer_port.CockpitMultiplexerSession(
            session_name="scratch", windows=()
        )
    ]


def test_output_that_is_not_a_herdr_reply_yields_no_sessions_instead_of_raising():
    assert cockpit_herdr_snapshot.parse_herdr_runtime_snapshot("") == []
    assert cockpit_herdr_snapshot.parse_herdr_runtime_snapshot("herdr: no server") == []
    assert cockpit_herdr_snapshot.parse_herdr_runtime_snapshot("[]") == []


def test_workspace_identifiers_resolve_by_label_so_mutations_can_target_them():
    assert cockpit_herdr_snapshot.parse_herdr_workspace_identifiers(
        DOTFILES_SNAPSHOT_OUTPUT
    ) == {"dotfiles": "w1T", "clawde": "w1P"}


def test_the_first_workspace_wins_when_two_share_a_label():
    workspace_identifiers = cockpit_herdr_snapshot.parse_herdr_workspace_identifiers(
        build_runtime_snapshot_output(
            workspaces=[
                {"workspace_id": "wA", "label": "dotfiles"},
                {"workspace_id": "wB", "label": "dotfiles"},
            ],
            tabs=[],
        )
    )

    assert workspace_identifiers == {"dotfiles": "wA"}
