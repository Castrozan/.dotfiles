#!/usr/bin/env python3

from __future__ import annotations

import sys

from catalog import select_servant_for_session


def main(argv: list[str]) -> int:
    session_id = argv[1] if len(argv) > 1 else ""
    if not session_id:
        return 1
    print(select_servant_for_session(session_id)["name"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
