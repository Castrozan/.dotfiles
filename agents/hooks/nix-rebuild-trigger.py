#!/usr/bin/env python3

import json
import os
import sys

NIX_FILE_EXTENSIONS = [
    ".nix",
]

PATHS_REQUIRING_SYSTEM_REBUILD = [
    ".dotfiles",
    "/etc/nixos",
    "configuration.nix",
    "hardware-configuration.nix",
    "flake.nix",
    "flake.lock",
    "home.nix",
    "default.nix",
    "shell.nix",
    "/home/zanoni/.dotfiles",
]


def has_nix_file_extension(path: str) -> bool:
    if not path:
        return False

    for extension in NIX_FILE_EXTENSIONS:
        if path.endswith(extension):
            return True

    return False


def is_system_configuration_path(path: str) -> bool:
    if not path:
        return False

    for system_path in PATHS_REQUIRING_SYSTEM_REBUILD:
        if system_path in path:
            return True

    return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)

    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not file_path:
        sys.exit(0)

    if not has_nix_file_extension(file_path):
        sys.exit(0)

    mandatory_rebuild_message = (
        f"MANDATORY: {os.path.basename(file_path)} changed. "
        "You MUST stage, commit, and run /rebuild "
        "before responding to the user. "
        "Do not skip. Untested nix changes are not changes."
    )
    output = {
        "continue": True,
        "systemMessage": mandatory_rebuild_message,
    }
    print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
