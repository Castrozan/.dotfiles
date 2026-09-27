import json
import sys

import tomli_w


def main():
    generated = json.load(sys.stdin)
    requirements = {"features": {"hooks": True}, "hooks": generated["hooks"]}
    sys.stdout.write(tomli_w.dumps(requirements))


if __name__ == "__main__":
    main()
