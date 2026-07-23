import re
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
PRIVATE_DISCORD_IDENTITY_PATH = (
    REPOSITORY_ROOT / "private-config" / "clawde-discord-identity.nix"
)
PRIVATE_SUBMODULE_DIRECTORY_NAME = "private-config"


def read_private_discord_user_id():
    identity_source = PRIVATE_DISCORD_IDENTITY_PATH.read_text()
    match = re.search(r'lucasDiscordUserId\s*=\s*"(\d+)"', identity_source)
    if match is None:
        pytest.skip("private-config no longer declares lucasDiscordUserId")
    return match.group(1)


def list_public_tracked_files():
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=True,
    )
    return [
        REPOSITORY_ROOT / relative_path
        for relative_path in completed.stdout.decode().split("\0")
        if relative_path
        and not relative_path.startswith(f"{PRIVATE_SUBMODULE_DIRECTORY_NAME}/")
        and relative_path != PRIVATE_SUBMODULE_DIRECTORY_NAME
    ]


def files_containing(needle, candidate_paths):
    encoded_needle = needle.encode()
    matches = []
    for candidate_path in candidate_paths:
        if not candidate_path.is_file():
            continue
        if encoded_needle in candidate_path.read_bytes():
            matches.append(str(candidate_path.relative_to(REPOSITORY_ROOT)))
    return matches


class TestPublicTreeExcludesPrivateDiscordIdentity:
    def test_no_public_tracked_file_contains_the_owner_discord_user_id(self):
        if not PRIVATE_DISCORD_IDENTITY_PATH.is_file():
            pytest.skip("private-config submodule is not checked out")
        private_discord_user_id = read_private_discord_user_id()
        leaking_paths = files_containing(
            private_discord_user_id, list_public_tracked_files()
        )
        assert leaking_paths == [], (
            "the owner's real Discord user id lives in the private-config submodule "
            "and must never appear in the public repository; found it in: "
            + ", ".join(leaking_paths)
        )
