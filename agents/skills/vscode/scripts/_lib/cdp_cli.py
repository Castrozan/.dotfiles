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
command_by_title, click, type, screenshot, snapshot, agent,
dismiss_modals, probe_chat_dom). The script is invoked via
`uv run --script` so the websocket-client/requests dependencies resolve
transparently on every call.
"""

from __future__ import annotations

import argparse
import base64
import json
import string
import sys
import time
from pathlib import Path
from typing import Any

import requests
from websocket import WebSocket, create_connection

PROBE_CHAT_DOM_JAVASCRIPT_TEMPLATE = string.Template(
    (Path(__file__).parent / "probe_chat_dom.js").read_text(encoding="utf-8")
)


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


def _break_focus_from_chat_panel(
    client: ChromeDevToolsClient, socket: WebSocket
) -> None:
    """Drop input focus from whatever panel currently holds it (chat input,
    terminal, search box, etc.) so the next keyboard chord reaches the
    workbench keybinding service instead of being typed as text.

    Tries, in order:
      1. The center of `.menubar` via a synthetic mouse click — if it
         exists in the DOM with non-zero size. This was the original
         strategy and is the most natural focus break.
      2. `document.body.focus()` via Runtime.evaluate. Works regardless
         of layout: zen mode, hidden menu bar, custom title bar style.
         The previous coordinate fallback `(10, 10)` was unsafe — on the
         default Linux build it lands on the first Activity Bar icon and
         opens/toggles the Explorer panel, which is a real side effect.
    """
    focus_attempt_result = client.send_and_wait(
        socket,
        "Runtime.evaluate",
        {
            "expression": (
                "(() => {"
                "  const menubar = document.querySelector('.menubar');"
                "  if (menubar) {"
                "    const r = menubar.getBoundingClientRect();"
                "    if (r.width > 0 && r.height > 0) {"
                "      return JSON.stringify({strategy: 'menubar_click', x: r.left + r.width/2, y: r.top + r.height/2});"
                "    }"
                "  }"
                "  document.body.focus();"
                "  if (document.activeElement && document.activeElement.blur) {"
                "    document.activeElement.blur();"
                "  }"
                "  return JSON.stringify({strategy: 'document_body_focus'});"
                "})()"
            ),
            "returnByValue": True,
        },
    )
    payload = json.loads(focus_attempt_result.get("result", {}).get("value", "{}"))
    if payload.get("strategy") == "menubar_click":
        _click_at_coordinate(
            client, socket, x=float(payload["x"]), y=float(payload["y"])
        )


def _open_command_palette(client: ChromeDevToolsClient, socket: WebSocket) -> None:
    # Sidebars and panels (Chat, Search, Terminal) keep input focus across
    # keyboard chords, swallowing Ctrl+Shift+P as text. Break focus first via
    # a menu-bar click (preferred — natural workbench focus) or a programmatic
    # blur as a layout-agnostic fallback.
    _break_focus_from_chat_panel(client, socket)
    time.sleep(0.15)
    _send_key_chord(client, socket, "Escape", 27)
    time.sleep(0.1)
    # Ctrl(2) + Shift(8) = 10. Lowercase 'p' on a US layout, virtual key 80.
    _send_key_chord(client, socket, "P", 80, modifiers=10)
    time.sleep(0.4)


def dismiss_modals(client: ChromeDevToolsClient, press_count: int) -> None:
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        for _ in range(press_count):
            _send_key_chord(client, socket, "Escape", 27)
            time.sleep(0.15)
    finally:
        socket.close()
    print(json.dumps({"ok": True, "presses": press_count}))


def run_command_by_title(client: ChromeDevToolsClient, command_title: str) -> None:
    """Execute a VS Code command by typing its visible **title** into the
    Command Palette (Ctrl+Shift+P) and pressing Enter.

    NOT a wrapper around `vscode.commands.executeCommand` — that API is
    only reachable from the Extension Host, which CDP cannot attach to.
    We drive the palette UI by simulated keyboard input, which means:

      - The argument is the user-visible **title** (e.g. "Preferences:
        Open Settings (UI)"), NOT the internal command id
        (`workbench.action.openSettings`). Internal ids don't render in
        the palette unless an extension explicitly registers them.
      - The title is **locale-dependent**. A pt-BR VS Code shows
        "Preferências: Abrir Configurações (UI)", which the en-US title
        won't match. Match the locale of the running editor.
      - There is no way to pass command arguments — the palette only
        invokes the command with its default arguments.

    If you need a real argument-passing executeCommand bridge, write a
    VS Code extension that exposes a port; this verb is intentionally
    the cheap "drive the UI" path.
    """
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        _open_command_palette(client, socket)
        _insert_text(client, socket, command_title)
        time.sleep(0.3)
        _send_key_chord(client, socket, "Enter", 13)
    finally:
        socket.close()
    print(json.dumps({"ok": True, "command_title": command_title}))


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


# Selectors pinned 2026-05-19 against VS Code 1.119.0 with the
# Claude Code extension active. Update docs/CDP-SELECTORS.md if Anthropic
# ships a UI refresh and any of these stop resolving.
CHAT_INPUT_EDITOR_SELECTOR = ".interactive-input-editor"
CHAT_SEND_BUTTON_SELECTOR = ".chat-execute-toolbar .action-label.codicon-arrow-up"
CHAT_STOP_BUTTON_SELECTOR = (
    ".chat-execute-toolbar .action-label.codicon-stop-circle,"
    " .chat-execute-toolbar .action-label.codicon-debug-stop,"
    " .chat-execute-toolbar .action-label.codicon-stop"
)
CHAT_ASSISTANT_MESSAGE_SELECTOR = ".interactive-list .interactive-response"


def _ensure_chat_panel_focused(client: ChromeDevToolsClient, socket: WebSocket) -> None:
    locate_result = client.send_and_wait(
        socket,
        "Runtime.evaluate",
        {
            "expression": (
                "(() => {"
                f" const el = document.querySelector({json.dumps(CHAT_INPUT_EDITOR_SELECTOR)});"
                " if (!el) return JSON.stringify({ok: false, error: 'chat input editor not found'});"
                " const r = el.getBoundingClientRect();"
                " if (r.width === 0) return JSON.stringify({ok: false, error: 'chat input editor not visible'});"
                " return JSON.stringify({ok: true, cx: Math.round(r.left + r.width/2), cy: Math.round(r.top + r.height/2)});"
                "})()"
            ),
            "returnByValue": True,
        },
    )
    payload = json.loads(locate_result.get("result", {}).get("value", "{}"))
    if not payload.get("ok"):
        raise SystemExit(
            f"Claude Code chat input not reachable: {payload.get('error', 'unknown')}"
        )
    _click_at_coordinate(client, socket, payload["cx"], payload["cy"])
    time.sleep(0.25)


def _read_chat_state(client: ChromeDevToolsClient, socket: WebSocket) -> dict[str, Any]:
    expression = (
        "JSON.stringify({"
        f"  stop_visible: !!document.querySelector({json.dumps(CHAT_STOP_BUTTON_SELECTOR)}),"
        f"  send_present: !!document.querySelector({json.dumps(CHAT_SEND_BUTTON_SELECTOR)}),"
        f"  send_disabled: (() => {{ const b = document.querySelector({json.dumps(CHAT_SEND_BUTTON_SELECTOR)}); return b ? b.classList.contains('disabled') : null; }})(),"
        f"  assistant_message_count: document.querySelectorAll({json.dumps(CHAT_ASSISTANT_MESSAGE_SELECTOR)}).length,"
        f"  last_assistant_text: (() => {{ const m = document.querySelectorAll({json.dumps(CHAT_ASSISTANT_MESSAGE_SELECTOR)}); return m.length ? (m[m.length-1].innerText || '').slice(-2000) : ''; }})()"
        "})"
    )
    result = client.send_and_wait(
        socket,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
    )
    return json.loads(result.get("result", {}).get("value", "{}"))


def agent_send_message(client: ChromeDevToolsClient, message: str) -> None:
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        _ensure_chat_panel_focused(client, socket)
        _insert_text(client, socket, message)
        time.sleep(0.4)
        # Send button transitions from `disabled` to enabled once text is present.
        for _ in range(10):
            state = _read_chat_state(client, socket)
            if state.get("send_present") and not state.get("send_disabled"):
                break
            time.sleep(0.2)
        click_result = client.send_and_wait(
            socket,
            "Runtime.evaluate",
            {
                "expression": (
                    "(() => {"
                    f" const b = document.querySelector({json.dumps(CHAT_SEND_BUTTON_SELECTOR)});"
                    " if (!b) return JSON.stringify({ok: false, error: 'send button not found'});"
                    " if (b.classList.contains('disabled')) return JSON.stringify({ok: false, error: 'send button still disabled after typing'});"
                    " b.click();"
                    " return JSON.stringify({ok: true});"
                    "})()"
                ),
                "returnByValue": True,
            },
        )
        payload = json.loads(click_result.get("result", {}).get("value", "{}"))
        if not payload.get("ok"):
            raise SystemExit(f"agent send failed: {payload.get('error', 'unknown')}")
    finally:
        socket.close()
    print(json.dumps({"ok": True, "subverb": "send", "characters": len(message)}))


def agent_state(client: ChromeDevToolsClient) -> None:
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        state = _read_chat_state(client, socket)
    finally:
        socket.close()
    payload = {
        "ok": True,
        "running": bool(state.get("stop_visible")),
        "assistant_messages": state.get("assistant_message_count", 0),
        "send_disabled": state.get("send_disabled"),
    }
    print(json.dumps(payload))


REQUIRED_CONSECUTIVE_IDLE_POLLS_FOR_STABILITY = 3


def _open_renderer_socket(client: ChromeDevToolsClient) -> WebSocket:
    page = client.find_renderer_page()
    return client.open_socket(page["webSocketDebuggerUrl"])


def _close_socket_quietly(socket: WebSocket | None) -> None:
    if socket is None:
        return
    try:
        socket.close()
    except Exception:
        # The socket may already be half-closed by the server; we are
        # discarding it anyway, so swallow whatever raises here.
        pass


def agent_wait_idle(
    client: ChromeDevToolsClient, timeout_seconds: int, poll_seconds: int
) -> None:
    """Block until the chat panel has been idle (no stop button visible and
    no new assistant messages) across `REQUIRED_CONSECUTIVE_IDLE_POLLS_FOR_STABILITY`
    consecutive polls.

    The single-poll signal `running=false` is unreliable: between two
    sequential tool calls within one assistant turn the stop button briefly
    disappears. Requiring multiple consecutive stable polls collapses that
    race — Claude needs to genuinely stay idle for at least
    (REQUIRED_CONSECUTIVE_IDLE_POLLS_FOR_STABILITY * poll_seconds) seconds
    before we declare the turn complete.

    Holds one WebSocket across the full poll loop so a long wait (e.g. 4h
    @ 30s poll = 480 polls) does not produce a connect/disconnect storm.
    The socket is transparently reopened if a poll throws (page reload,
    transient network blip) so a long watch is not crashed by one error.
    """
    socket: WebSocket | None = _open_renderer_socket(client)
    start_monotonic = time.monotonic()
    last_message_count = -1
    last_text = ""
    consecutive_stable_idle_polls = 0
    consecutive_socket_errors = 0
    MAX_CONSECUTIVE_SOCKET_ERRORS_BEFORE_GIVING_UP = 5
    try:
        while time.monotonic() - start_monotonic < timeout_seconds:
            try:
                state = _read_chat_state(client, socket)
                consecutive_socket_errors = 0
            except Exception as poll_error:
                consecutive_socket_errors += 1
                print(
                    json.dumps(
                        {
                            "elapsed_seconds": int(time.monotonic() - start_monotonic),
                            "socket_error": str(poll_error),
                            "consecutive_socket_errors": consecutive_socket_errors,
                            "action": "reopening socket",
                        }
                    ),
                    flush=True,
                )
                if (
                    consecutive_socket_errors
                    >= MAX_CONSECUTIVE_SOCKET_ERRORS_BEFORE_GIVING_UP
                ):
                    print(
                        json.dumps(
                            {
                                "ok": False,
                                "outcome": "socket_failure",
                                "consecutive_socket_errors": consecutive_socket_errors,
                                "last_error": str(poll_error),
                            }
                        )
                    )
                    sys.exit(3)
                _close_socket_quietly(socket)
                socket = None
                time.sleep(min(poll_seconds, 5))
                try:
                    socket = _open_renderer_socket(client)
                except Exception:
                    # Will try again on the next loop iteration.
                    pass
                continue

            running = bool(state.get("stop_visible"))
            message_count = state.get("assistant_message_count", 0)
            last_text = state.get("last_assistant_text", "")
            elapsed = int(time.monotonic() - start_monotonic)

            is_stable_idle_poll = (
                not running
                and message_count > 0
                and message_count == last_message_count
            )
            if is_stable_idle_poll:
                consecutive_stable_idle_polls += 1
            else:
                consecutive_stable_idle_polls = 0

            print(
                json.dumps(
                    {
                        "elapsed_seconds": elapsed,
                        "running": running,
                        "assistant_messages": message_count,
                        "consecutive_stable_idle_polls": consecutive_stable_idle_polls,
                    }
                ),
                flush=True,
            )

            if (
                consecutive_stable_idle_polls
                >= REQUIRED_CONSECUTIVE_IDLE_POLLS_FOR_STABILITY
            ):
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "outcome": "idle",
                            "elapsed_seconds": elapsed,
                            "assistant_messages": message_count,
                            "last_assistant_tail": last_text,
                        }
                    )
                )
                return

            last_message_count = message_count
            time.sleep(poll_seconds)
    finally:
        _close_socket_quietly(socket)
    print(
        json.dumps(
            {
                "ok": False,
                "outcome": "timeout",
                "timeout_seconds": timeout_seconds,
                "last_assistant_tail": last_text,
            }
        )
    )
    sys.exit(2)


def probe_chat_dom(client: ChromeDevToolsClient) -> None:
    """Re-discover Claude Code chat selectors against the live DOM.

    Consolidates the five one-off probe scripts (probe-inputs.py,
    probe-chat.py, probe-input-area.py, probe-chat-input.py,
    probe-messages.py) that were used 2026-05-19 to pin the selectors
    currently in CHAT_*_SELECTOR. Run this after a VS Code or Claude
    Code extension update if `agent state` / `agent send` start failing
    — the JSON output shows which selectors still resolve and where
    they live, so docs/CDP-SELECTORS.md can be refreshed.
    """
    expression = PROBE_CHAT_DOM_JAVASCRIPT_TEMPLATE.substitute(
        INPUT_SELECTOR=json.dumps(CHAT_INPUT_EDITOR_SELECTOR),
        SEND_SELECTOR=json.dumps(CHAT_SEND_BUTTON_SELECTOR),
        STOP_SELECTOR=json.dumps(CHAT_STOP_BUTTON_SELECTOR),
        ASSISTANT_SELECTOR=json.dumps(CHAT_ASSISTANT_MESSAGE_SELECTOR),
    )
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        result = client.send_and_wait(
            socket,
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
        )
        report = json.loads(result.get("result", {}).get("value", "{}"))
        # Inject the pinned constants so reviewers can diff at a glance.
        report["_pinned_constants"] = {
            "CHAT_INPUT_EDITOR_SELECTOR": CHAT_INPUT_EDITOR_SELECTOR,
            "CHAT_SEND_BUTTON_SELECTOR": CHAT_SEND_BUTTON_SELECTOR,
            "CHAT_STOP_BUTTON_SELECTOR": CHAT_STOP_BUTTON_SELECTOR,
            "CHAT_ASSISTANT_MESSAGE_SELECTOR": CHAT_ASSISTANT_MESSAGE_SELECTOR,
        }
    finally:
        socket.close()
    print(json.dumps(report, indent=2))


def agent_read_last(client: ChromeDevToolsClient) -> None:
    page = client.find_renderer_page()
    socket = client.open_socket(page["webSocketDebuggerUrl"])
    try:
        state = _read_chat_state(client, socket)
    finally:
        socket.close()
    print(
        json.dumps(
            {
                "ok": True,
                "assistant_messages": state.get("assistant_message_count", 0),
                "last_assistant_text": state.get("last_assistant_text", ""),
            }
        )
    )


def dispatch_agent_subverb(
    client: ChromeDevToolsClient, subverb: str, extra_args: argparse.Namespace
) -> None:
    if subverb == "send":
        if not extra_args.message:
            raise SystemExit("--message is required for agent send")
        agent_send_message(client, extra_args.message)
        return
    if subverb == "state":
        agent_state(client)
        return
    if subverb == "read":
        agent_read_last(client)
        return
    if subverb == "wait-idle":
        timeout = int(extra_args.timeout or 1800)
        poll = int(extra_args.poll or 20)
        agent_wait_idle(client, timeout, poll)
        return
    # Unimplemented subverbs still return a clear stub error.
    print(
        json.dumps(
            {
                "ok": False,
                "subverb": subverb,
                "error": (
                    f"agent subverb '{subverb}' not implemented yet. "
                    "Implemented: send, state, read, wait-idle. "
                    "Pending: new, transcript, history (need additional selector pinning — see docs/CDP-SELECTORS.md)."
                ),
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
            "command_by_title",
            "click",
            "type",
            "screenshot",
            "snapshot",
            "agent",
            "dismiss_modals",
            "probe_chat_dom",
        ],
        required=True,
    )
    parser.add_argument(
        "--presses", help="Escape press count for dismiss_modals", default="3"
    )
    parser.add_argument(
        "--command-title", help="VS Code command title for command_by_title"
    )
    parser.add_argument("--selector", help="CSS selector for click/type")
    parser.add_argument("--text", help="Text to type")
    parser.add_argument("--out", help="Output path for screenshot")
    parser.add_argument("--full", help="Full-page screenshot flag")
    parser.add_argument("--subverb", help="Agent subverb")
    parser.add_argument("--message", help="Agent send: message body")
    parser.add_argument("--timeout", help="Agent wait-idle: max seconds")
    parser.add_argument("--poll", help="Agent wait-idle: poll interval seconds")
    args = parser.parse_args()

    client = ChromeDevToolsClient(port=args.port)

    if args.entry == "format_pages":
        format_pages(client)
    elif args.entry == "command_by_title":
        if not args.command_title:
            raise SystemExit("--command-title is required for command_by_title")
        run_command_by_title(client, args.command_title)
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
    elif args.entry == "probe_chat_dom":
        probe_chat_dom(client)
    else:
        raise SystemExit(f"unknown entry: {args.entry}")


if __name__ == "__main__":
    main()
