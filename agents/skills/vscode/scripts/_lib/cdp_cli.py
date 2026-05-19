# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "websocket-client>=1.7",
#   "requests>=2.31",
# ]
# ///
"""CLI entry point that the bash dispatcher (`vscode`) shells out to.

Every subcommand reads `--port`, `--entry`, and any extra flags. The
`--entry` argument selects the high-level operation (format_pages,
run_command, palette, click, type, screenshot, snapshot, agent). The
script is invoked via `uv run --script` so the websocket-client/requests
dependencies resolve transparently on every call.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from typing import Any

import requests
from websocket import WebSocket, create_connection


class ChromeDevToolsClient:
    def __init__(self, port: int):
        self.port = port
        self._next_id = 0

    def http_json(self) -> list[dict[str, Any]]:
        response = requests.get(f"http://localhost:{self.port}/json", timeout=5)
        response.raise_for_status()
        return response.json()

    def find_renderer_page(self) -> dict[str, Any]:
        pages = self.http_json()
        renderers = [
            page
            for page in pages
            if page.get("type") == "page"
            and "webSocketDebuggerUrl" in page
            and not page.get("url", "").startswith("devtools://")
        ]
        if not renderers:
            raise SystemExit("no renderer page available on this CDP endpoint")
        return renderers[0]

    def find_page_by_url_pattern(self, url_substring: str) -> dict[str, Any] | None:
        for page in self.http_json():
            if url_substring in page.get("url", ""):
                return page
        return None

    def open_socket(self, websocket_debugger_url: str) -> WebSocket:
        return create_connection(websocket_debugger_url, timeout=10)

    def send_and_wait(
        self, socket: WebSocket, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self._next_id += 1
        message_id = self._next_id
        socket.send(
            json.dumps({"id": message_id, "method": method, "params": params or {}})
        )
        while True:
            raw = socket.recv()
            if not raw:
                continue
            payload = json.loads(raw)
            if payload.get("id") == message_id:
                if "error" in payload:
                    raise SystemExit(f"CDP error from {method}: {payload['error']}")
                return payload.get("result", {})


def format_pages(client: ChromeDevToolsClient) -> None:
    pages = client.http_json()
    for page in pages:
        page_type = page.get("type", "?")
        url = page.get("url", "")
        title = page.get("title", "")
        print(f"  [{page_type}] {title} :: {url}")


def evaluate_javascript_in_active_page(
    client: ChromeDevToolsClient, expression: str, await_promise: bool = True
) -> dict[str, Any]:
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        return client.send_and_wait(
            socket,
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": await_promise,
                "returnByValue": True,
            },
        )
    finally:
        socket.close()


def _send_key_chord(
    client: ChromeDevToolsClient,
    socket: WebSocket,
    key: str,
    virtual_key_code: int,
    modifiers: int = 0,
) -> None:
    client.send_and_wait(
        socket,
        "Input.dispatchKeyEvent",
        {
            "type": "keyDown",
            "key": key,
            "windowsVirtualKeyCode": virtual_key_code,
            "modifiers": modifiers,
        },
    )
    client.send_and_wait(
        socket,
        "Input.dispatchKeyEvent",
        {
            "type": "keyUp",
            "key": key,
            "windowsVirtualKeyCode": virtual_key_code,
            "modifiers": modifiers,
        },
    )


def _insert_text(client: ChromeDevToolsClient, socket: WebSocket, text: str) -> None:
    client.send_and_wait(socket, "Input.insertText", {"text": text})


def _click_at_coordinate(
    client: ChromeDevToolsClient, socket: WebSocket, x: float, y: float
) -> None:
    for event_type in ("mousePressed", "mouseReleased"):
        client.send_and_wait(
            socket,
            "Input.dispatchMouseEvent",
            {
                "type": event_type,
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1,
            },
        )


def _open_command_palette(client: ChromeDevToolsClient, socket: WebSocket) -> None:
    import time

    # Sidebars and panels (Chat, Search, Terminal) keep input focus across
    # keyboard chords, swallowing Ctrl+Shift+P as text. A mouse click on the
    # menu bar reliably moves focus to the workbench shell without disturbing
    # any open editor. Menu bar is the top ~22 px of the window.
    _click_at_coordinate(client, socket, x=400, y=8)
    time.sleep(0.15)
    _send_key_chord(client, socket, "Escape", 27)
    time.sleep(0.1)
    # Ctrl(2) + Shift(8) = 10. Lowercase 'p' on a US layout, virtual key 80.
    _send_key_chord(client, socket, "P", 80, modifiers=10)
    time.sleep(0.4)


def dismiss_modals(client: ChromeDevToolsClient, press_count: int) -> None:
    import time

    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        for _ in range(press_count):
            _send_key_chord(client, socket, "Escape", 27)
            time.sleep(0.15)
    finally:
        socket.close()
    print(json.dumps({"ok": True, "presses": press_count}))


def run_vscode_command(
    client: ChromeDevToolsClient, command_id: str, command_args_json: str | None
) -> None:
    if command_args_json:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "command args are not supported via the palette path",
                }
            )
        )
        sys.exit(1)
    import time

    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        _open_command_palette(client, socket)
        _insert_text(client, socket, command_id)
        time.sleep(0.3)
        _send_key_chord(client, socket, "Enter", 13)
    finally:
        socket.close()
    print(json.dumps({"ok": True, "command": command_id, "via": "palette"}))


def open_command_palette_and_run(client: ChromeDevToolsClient, query: str) -> None:
    import time

    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        _open_command_palette(client, socket)
        _insert_text(client, socket, query)
        time.sleep(0.3)
        _send_key_chord(client, socket, "Enter", 13)
    finally:
        socket.close()
    print(json.dumps({"ok": True, "query": query}))


def click_by_css_selector(client: ChromeDevToolsClient, selector: str) -> None:
    expression = (
        "(() => {"
        f" const element = document.querySelector({json.dumps(selector)});"
        " if (!element) return JSON.stringify({ok: false, error: 'selector not found'});"
        " element.click();"
        " return JSON.stringify({ok: true});"
        "})()"
    )
    result = evaluate_javascript_in_active_page(client, expression, await_promise=False)
    value = result.get("result", {}).get("value", "{}")
    print(value)


def type_into_css_selector(
    client: ChromeDevToolsClient, selector: str, text: str
) -> None:
    expression = (
        "(() => {"
        f" const element = document.querySelector({json.dumps(selector)});"
        " if (!element) return JSON.stringify({ok: false, error: 'selector not found'});"
        " element.focus();"
        f" const text = {json.dumps(text)};"
        " if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {"
        "   element.value = (element.value || '') + text;"
        "   element.dispatchEvent(new Event('input', {bubbles: true}));"
        " } else if (element.isContentEditable) {"
        "   document.execCommand('insertText', false, text);"
        " }"
        " return JSON.stringify({ok: true});"
        "})()"
    )
    result = evaluate_javascript_in_active_page(client, expression, await_promise=False)
    value = result.get("result", {}).get("value", "{}")
    print(value)


def capture_screenshot(
    client: ChromeDevToolsClient, output_path: str, capture_full_document: bool
) -> None:
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        capture_params: dict[str, Any] = {"format": "png"}
        if capture_full_document:
            capture_params["captureBeyondViewport"] = True
        result = client.send_and_wait(socket, "Page.captureScreenshot", capture_params)
    finally:
        socket.close()
    data_base64 = result.get("data")
    if not data_base64:
        raise SystemExit("CDP returned no screenshot data")
    with open(output_path, "wb") as handle:
        handle.write(base64.b64decode(data_base64))


def capture_accessibility_snapshot(client: ChromeDevToolsClient) -> None:
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        client.send_and_wait(socket, "Accessibility.enable")
        result = client.send_and_wait(socket, "Accessibility.getFullAXTree")
    finally:
        socket.close()
    print(json.dumps(result, indent=2))


def dispatch_agent_subverb(
    client: ChromeDevToolsClient, subverb: str, extra_args: argparse.Namespace
) -> None:
    # The Claude Code WebView selectors are not yet pinned — this is a v1 stub
    # that returns a clear error so callers know to follow up with selector discovery.
    print(
        json.dumps(
            {
                "ok": False,
                "subverb": subverb,
                "error": (
                    "agent verbs are stubbed in v1 — selectors for the Claude Code WebView need to be "
                    "discovered against a running VS Code with the extension active. Run `vscode launch` "
                    "and then `vscode cdp-pages --raw` to see the available WebView pages, capture a "
                    "snapshot, and pin the selectors in docs/CDP-SELECTORS.md."
                ),
                "next_steps": [
                    "vscode launch",
                    "vscode cdp-pages --raw",
                    "(open Claude Code panel in VS Code)",
                    "vscode snapshot > /tmp/claude-code-snapshot.json",
                    "inspect snapshot for input box / send button selectors",
                ],
            },
            indent=2,
        )
    )
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument(
        "--entry",
        choices=[
            "format_pages",
            "run_command",
            "palette",
            "click",
            "type",
            "screenshot",
            "snapshot",
            "agent",
            "dismiss_modals",
        ],
        required=True,
    )
    parser.add_argument(
        "--presses", help="Escape press count for dismiss_modals", default="3"
    )
    parser.add_argument("--command", help="VS Code command id for run_command")
    parser.add_argument("--args", help="JSON-encoded args for run_command")
    parser.add_argument("--query", help="Palette query")
    parser.add_argument("--selector", help="CSS selector for click/type")
    parser.add_argument("--text", help="Text to type")
    parser.add_argument("--out", help="Output path for screenshot")
    parser.add_argument("--full", help="Full-page screenshot flag")
    parser.add_argument("--subverb", help="Agent subverb")
    parser.add_argument("--since", help="Agent read: messages since N")
    parser.add_argument("--session-id", help="Agent transcript: session id")
    parser.add_argument("--message", help="Agent send: message body")
    args = parser.parse_args()

    client = ChromeDevToolsClient(port=args.port)

    if args.entry == "format_pages":
        format_pages(client)
    elif args.entry == "run_command":
        if not args.command:
            raise SystemExit("--command is required for run_command")
        run_vscode_command(client, args.command, args.args)
    elif args.entry == "palette":
        if not args.query:
            raise SystemExit("--query is required for palette")
        open_command_palette_and_run(client, args.query)
    elif args.entry == "click":
        if not args.selector:
            raise SystemExit("--selector is required for click")
        click_by_css_selector(client, args.selector)
    elif args.entry == "type":
        if not args.selector or args.text is None:
            raise SystemExit("--selector and --text are required for type")
        type_into_css_selector(client, args.selector, args.text)
    elif args.entry == "screenshot":
        if not args.out:
            raise SystemExit("--out is required for screenshot")
        capture_screenshot(client, args.out, args.full == "true")
    elif args.entry == "snapshot":
        capture_accessibility_snapshot(client)
    elif args.entry == "agent":
        dispatch_agent_subverb(client, args.subverb or "", args)
    elif args.entry == "dismiss_modals":
        dismiss_modals(client, int(args.presses))
    else:
        raise SystemExit(f"unknown entry: {args.entry}")


if __name__ == "__main__":
    main()
