"""Long-running CDP XHR listener for B3 portal exploration.

Connects to browser-use's Chrome (default port 52785, or first found chrome with
remote-debugging), enables Network domain, then loops forever capturing every
investidor.b3.com.br XHR/Fetch response body. Writes one JSON file per request,
plus an append-only summary.txt, into data/raw/b3/<today>/explore/.

Browser navigation is done externally (via browser-use MCP); this script only
listens.

Stop with SIGINT.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import signal
from datetime import date, datetime
from pathlib import Path

import httpx
import websockets

WORKSPACE_ROOT = Path(
    os.environ.get(
        "B3_WORKSPACE_ROOT",
        str(Path.home() / ".claude-discord-agents" / "golden"),
    )
)
OUTPUT_DIRECTORY = (
    WORKSPACE_ROOT / "data" / "raw" / "b3" / date.today().isoformat() / "explore"
)
OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = OUTPUT_DIRECTORY / "summary.txt"


def discover_chrome_debugger_port() -> int:
    import subprocess

    explicit_port = os.environ.get("B3_CHROME_PORT")
    candidate_ports: list[int] = []
    if explicit_port:
        candidate_ports.append(int(explicit_port))
    try:
        pgrep_output = subprocess.run(
            ["pgrep", "-af", "browser-use-user-data-dir"],
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout
        import re

        for match in re.finditer(r"remote-debugging-port=(\d+)", pgrep_output):
            candidate_ports.append(int(match.group(1)))
    except Exception:
        pass
    candidate_ports.extend([52785, 9222, 9223])
    seen_ports: set[int] = set()
    for candidate_port in candidate_ports:
        if candidate_port in seen_ports:
            continue
        seen_ports.add(candidate_port)
        try:
            response = httpx.get(
                f"http://localhost:{candidate_port}/json/version", timeout=2
            )
            if response.status_code == 200:
                return candidate_port
        except httpx.HTTPError:
            continue
    raise SystemExit(f"no Chrome found among {sorted(seen_ports)}")


def find_b3_tab_websocket_url(chrome_debugger_port: int) -> str:
    open_tabs = httpx.get(
        f"http://localhost:{chrome_debugger_port}/json", timeout=5
    ).json()
    b3_tabs = [
        tab
        for tab in open_tabs
        if tab.get("type") == "page" and "investidor.b3" in tab.get("url", "")
    ]
    if not b3_tabs:
        raise SystemExit("no investidor.b3 tab open")
    return b3_tabs[0]["webSocketDebuggerUrl"]


async def listen_for_b3_xhrs() -> None:
    chrome_debugger_port = discover_chrome_debugger_port()
    tab_websocket_url = find_b3_tab_websocket_url(chrome_debugger_port)
    print(f"attached: port={chrome_debugger_port} ws={tab_websocket_url}", flush=True)

    next_command_id = [10000]
    pending_body_fetches: dict[int, str] = {}
    captured_request_urls_by_id: dict[str, dict] = {}
    written_paths: set[str] = set()
    stop_event = asyncio.Event()

    def request_stop(*_args):
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    async with websockets.connect(
        tab_websocket_url, max_size=64 * 1024 * 1024
    ) as websocket:

        async def send_command(method: str, params: dict | None = None) -> int:
            next_command_id[0] += 1
            command_id = next_command_id[0]
            await websocket.send(
                json.dumps({"id": command_id, "method": method, "params": params or {}})
            )
            return command_id

        await send_command("Network.enable")
        await send_command("Page.enable")

        request_counter = 0
        while not stop_event.is_set():
            try:
                raw_message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            message = json.loads(raw_message)
            if "id" in message:
                if message["id"] in pending_body_fetches:
                    request_id = pending_body_fetches.pop(message["id"])
                    request_info = captured_request_urls_by_id.get(request_id)
                    if not request_info:
                        continue
                    result = message.get("result", {})
                    response_body_text = result.get("body", "")
                    if result.get("base64Encoded"):
                        try:
                            response_body_text = base64.b64decode(
                                response_body_text
                            ).decode("utf-8", errors="replace")
                        except Exception:
                            pass
                    timestamp_label = datetime.now().strftime("%H%M%S")
                    safe_segment = (
                        request_info["url"]
                        .split("?")[0]
                        .split("/api/")[-1]
                        .replace("/", "__")
                        .replace(".", "_")
                    )[:80]
                    body_path = (
                        OUTPUT_DIRECTORY
                        / f"{timestamp_label}_{request_counter:04d}_{safe_segment}.json"
                    )
                    request_counter += 1
                    body_path.write_text(response_body_text or "", encoding="utf-8")
                    written_paths.add(body_path.name)
                    with SUMMARY_PATH.open("a", encoding="utf-8") as summary_file:
                        summary_file.write(
                            f"{timestamp_label}  {request_info['method']:<5} {request_info['url']}  -> {body_path.name}\n"
                        )
                    print(
                        f"  saved {body_path.name}  <-  {request_info['url'][:120]}",
                        flush=True,
                    )
                continue
            event_method = message.get("method", "")
            params = message.get("params", {})
            if event_method == "Network.requestWillBeSent":
                request_url = params.get("request", {}).get("url", "")
                request_type = params.get("type", "")
                if (
                    request_type in ("XHR", "Fetch")
                    and "investidor.b3.com.br" in request_url
                ):
                    captured_request_urls_by_id[params["requestId"]] = {
                        "url": request_url,
                        "method": params["request"].get("method", "GET"),
                    }
            elif event_method == "Network.loadingFinished":
                request_id = params.get("requestId")
                if request_id in captured_request_urls_by_id:
                    body_command_id = await send_command(
                        "Network.getResponseBody", {"requestId": request_id}
                    )
                    pending_body_fetches[body_command_id] = request_id

    print(f"stopped. wrote {len(written_paths)} files to {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    asyncio.run(listen_for_b3_xhrs())
