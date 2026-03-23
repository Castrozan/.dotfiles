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

    if is_system_configuration_path(file_path):
        output = {
            "continue": True,
            "systemMessage": (
                f"NIX FILE CHANGED: {os.path.basename(file_path)}\n"
                "Remember to rebuild to apply changes:\n"
                "  - System: nixos-rebuild switch --flake .#\n"
                "  - Home: home-manager switch --flake .#\n"
                "  - Both: ./bin/rebuild or use the /rebuild skill"
            ),
        }
        print(json.dumps(output))
    else:
        output = {
            "continue": True,
            "systemMessage": (
                f"Nix file modified: {os.path.basename(file_path)}\n"
                "Run `nix flake check` or rebuild if this affects system config."
            ),
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
