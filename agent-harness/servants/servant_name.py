#!/usr/bin/env python3

"""The name of the Servant a session is, for callers that cannot import Python.

The Claude statusline redraws several times a minute holding nothing about the
session but its id, so it re-derives the name here rather than reading one the
SessionStart hook wrote down. That keeps a single implementation of the draw: the
name on screen is the one the session was given and cannot drift from it.

Prints nothing and exits non-zero without a session id, because every id-less caller
would otherwise be handed the same Servant.
"""

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
