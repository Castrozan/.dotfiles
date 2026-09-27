import json
import os
import sys
from pathlib import Path

import tomli_w


def confined_path(value, label):
    resolved = os.path.realpath(value)
    allowed_bases = (os.path.realpath(os.getcwd()), "/nix/store")
    if not any(
        resolved == base or resolved.startswith(base + os.sep) for base in allowed_bases
    ):
        raise ValueError(
            f"{label} must stay within the store or the invocation directory"
        )
    return Path(resolved)


def main():
    if len(sys.argv) != 3:
        raise ValueError("usage: codex_requirements.py <hooks-json> <output>")
    generated = json.loads(confined_path(sys.argv[1], "input").read_text())
    requirements = {"features": {"hooks": True}, "hooks": generated["hooks"]}
    confined_path(sys.argv[2], "output").write_text(tomli_w.dumps(requirements))


if __name__ == "__main__":
    main()
