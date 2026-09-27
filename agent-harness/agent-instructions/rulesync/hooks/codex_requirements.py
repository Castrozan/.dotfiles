import json
import os
import sys
from pathlib import Path

import tomli_w


def confined_path(value, label):
    path = Path(value)
    text = os.fspath(path)
    if not os.path.isabs(text) or ".." in path.parts:
        raise ValueError(f"{label} must be an absolute path without traversal segments")
    return path


def main():
    if len(sys.argv) != 3:
        raise ValueError("usage: codex_requirements.py <hooks-json> <output>")
    generated = json.loads(confined_path(sys.argv[1], "input").read_text())
    requirements = {"features": {"hooks": True}, "hooks": generated["hooks"]}
    confined_path(sys.argv[2], "output").write_text(tomli_w.dumps(requirements))


if __name__ == "__main__":
    main()
