#!/usr/bin/env python3
"""rebuild-notify.py - Notify before rebuild commands that will affect the system."""

import json
import re
import sys

REBUILD_PATTERNS = [
    (r"nixos-rebuild\s+switch", "NixOS system rebuild"),
    (r"nixos-rebuild\s+test", "NixOS test rebuild (not permanent)"),
    (r"nixos-rebuild\s+boot", "NixOS boot rebuild (activates on reboot)"),
    (r"home-manager\s+switch", "home-manager profile switch"),
    (r"nix\s+run\s+.*home-manager.*switch", "home-manager switch via nix run"),
    (r"*homeConfigurations*", "building home-manager configuration"),
    (r"*nixosConfigurations*", "building NixOS configuration"),
    (r"\./bin/rebuild", "dotfiles rebuild script"),
    (r"~/\.dotfiles/bin/rebuild", "dotfiles rebuild script"),
    (r"\$HOME/\.dotfiles/bin/rebuild", "dotfiles rebuild script"),
]


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    for pattern, description in REBUILD_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            output = {
                "continue": True,
                "systemMessage": (
                    f"REBUILD: {description}. "
                    "This will apply Nix configuration changes. Use /rebuild skill for guidance."
                )
            }
            print(json.dumps(output))
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
