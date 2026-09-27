import json
import sys
from pathlib import Path

import tomli_w


def main():
    generated = json.loads(Path(sys.argv[1]).read_text())
    requirements = {"features": {"hooks": True}, "hooks": generated["hooks"]}
    Path(sys.argv[2]).write_text(tomli_w.dumps(requirements))


if __name__ == "__main__":
    main()
