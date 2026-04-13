#!/usr/bin/env python3

import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = data.get("tool_name", "")

    if tool_name == "Grep":
        output = {
            "continue": True,
            "systemMessage": (
                "If you plan to edit any files from these "
                "results, call Read on each file first. "
                "Grep shows fragments. Read shows context."
            ),
        }
        print(json.dumps(output))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
