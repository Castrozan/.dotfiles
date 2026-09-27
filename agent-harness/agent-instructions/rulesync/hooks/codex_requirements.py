import json
import sys

import tomli_w


def _validated_hooks_payload(generated):
    hooks = generated.get("hooks") if isinstance(generated, dict) else None
    if not isinstance(hooks, dict):
        raise ValueError("Rulesync hooks payload is missing a 'hooks' object")
    return hooks


def main():
    generated = json.load(sys.stdin)
    requirements = {
        "features": {"hooks": True},
        "hooks": _validated_hooks_payload(generated),
    }
    sys.stdout.write(tomli_w.dumps(requirements))


if __name__ == "__main__":
    main()
