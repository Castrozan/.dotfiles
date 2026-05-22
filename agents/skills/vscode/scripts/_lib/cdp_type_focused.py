# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "websocket-client>=1.7",
#   "requests>=2.31",
# ]
# ///
"""Send Unicode text via CDP Input.insertText to whatever element currently
has focus in the VS Code renderer page.

Use when the target is a Monaco editor widget (e.g. the Extensions sidebar
search input, the workbench Search view input) where document.querySelector
+ .focus() + execCommand do not work because the input is a contenteditable
surface backed by Monaco rather than a plain HTMLInputElement. The caller
is responsible for ensuring focus is on the right element first, typically
by running a 'Focus on ... View' palette command immediately before.
"""

from __future__ import annotations

import argparse
import json
import sys

import requests
from websocket import create_connection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--text", required=True)
    args = parser.parse_args()

    pages_response = requests.get(f"http://localhost:{args.port}/json", timeout=5)
    pages_response.raise_for_status()
    renderer_pages = [
        page
        for page in pages_response.json()
        if page.get("type") == "page"
        and "webSocketDebuggerUrl" in page
        and not page.get("url", "").startswith("devtools://")
    ]
    if not renderer_pages:
        sys.exit("no renderer page available on this CDP endpoint")

    socket = create_connection(renderer_pages[0]["webSocketDebuggerUrl"], timeout=10)
    try:
        socket.send(
            json.dumps(
                {
                    "id": 1,
                    "method": "Input.insertText",
                    "params": {"text": args.text},
                }
            )
        )
        while True:
            raw = socket.recv()
            if not raw:
                continue
            payload = json.loads(raw)
            if payload.get("id") == 1:
                if "error" in payload:
                    sys.exit(f"CDP error from Input.insertText: {payload['error']}")
                break
    finally:
        socket.close()

    print(json.dumps({"ok": True, "characters": len(args.text)}))


if __name__ == "__main__":
    main()
