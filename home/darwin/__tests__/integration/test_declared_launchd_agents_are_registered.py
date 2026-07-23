import os
import plistlib
import subprocess
import sys
from pathlib import Path

import pytest

LAUNCH_AGENTS_DIRECTORY = Path.home() / "Library" / "LaunchAgents"
REPOSITORY_MANAGED_LABEL_PREFIXES = ("com.dotfiles.", "org.nix-community.home.")

pytestmark = pytest.mark.skipif(
    sys.platform != "darwin", reason="launchd user agents only exist on darwin"
)


def deployed_agent_plists() -> list[Path]:
    if not LAUNCH_AGENTS_DIRECTORY.is_dir():
        return []
    return sorted(
        path
        for path in LAUNCH_AGENTS_DIRECTORY.glob("*.plist")
        if path.stem.startswith(REPOSITORY_MANAGED_LABEL_PREFIXES)
    )


def agent_definition(plist_path: Path) -> dict:
    with plist_path.open("rb") as plist_file:
        return plistlib.load(plist_file)


def runs_once_per_login_session(definition: dict) -> bool:
    return bool(definition.get("LaunchOnlyOnce"))


def label_is_registered_with_launchd(label: str) -> bool:
    result = subprocess.run(
        ["launchctl", "print", f"gui/{os.getuid()}/{label}"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.returncode == 0


def test_the_launchd_agent_scan_finds_the_deployed_agents():
    assert len(deployed_agent_plists()) > 5, (
        f"no repository-managed agents found under {LAUNCH_AGENTS_DIRECTORY}, "
        f"so this suite would pass without checking anything"
    )


def test_every_agent_plist_declares_the_label_matching_its_filename():
    mismatched = [
        (plist_path.name, agent_definition(plist_path).get("Label"))
        for plist_path in deployed_agent_plists()
        if agent_definition(plist_path).get("Label") != plist_path.stem
    ]
    assert not mismatched, (
        f"these plists declare a label that does not match their filename, so "
        f"launchctl cannot be targeted by filename: {mismatched}"
    )


def test_every_long_running_declared_agent_is_registered_with_launchd():
    unregistered = []
    for plist_path in deployed_agent_plists():
        definition = agent_definition(plist_path)
        if runs_once_per_login_session(definition):
            continue
        label = definition.get("Label", plist_path.stem)
        if not label_is_registered_with_launchd(label):
            unregistered.append(label)
    assert not unregistered, (
        f"these agents are declared and deployed but absent from launchd, so they "
        f"are silently dead until the label is enabled and bootstrapped again: "
        f"{unregistered}"
    )
