import json
import subprocess
import time

TEST_WORKSPACE = 99
SETTLE_TIME = 0.4
SPAWN_SETTLE = 0.6


def hyprctl(*args: str) -> str:
    result = subprocess.run(["hyprctl", *args], capture_output=True, text=True)
    return result.stdout


def hyprctl_json(*args: str) -> dict | list | None:
    output = hyprctl(*args, "-j")
    try:
        return json.loads(output) if output.strip() else None
    except json.JSONDecodeError:
        return None


def dispatch(*args: str) -> None:
    hyprctl("dispatch", *args)
    time.sleep(SETTLE_TIME)


def get_clients_on_workspace(ws_id: int) -> list[dict]:
    clients = hyprctl_json("clients") or []
    return [
        c
        for c in clients
        if c.get("workspace", {}).get("id") == ws_id and not c.get("floating", False)
    ]


def get_focused_address() -> str:
    window = hyprctl_json("activewindow")
    return window.get("address", "") if window else ""


def get_focused_workspace_id() -> int:
    window = hyprctl_json("activewindow")
    if window:
        return window.get("workspace", {}).get("id", -1)
    return -1


def spawn_kitty(title: str) -> str:
    dispatch("workspace", str(TEST_WORKSPACE))
    dispatch("exec", f"kitty --title '{title}' -e sleep 300")
    time.sleep(SPAWN_SETTLE)
    clients = get_clients_on_workspace(TEST_WORKSPACE)
    for c in clients:
        if c.get("title") == title:
            return c["address"]
    if clients:
        return sorted(clients, key=lambda c: c.get("focusHistoryID", 9999))[0][
            "address"
        ]
    return ""


def focus_window(address: str) -> None:
    dispatch("focuswindow", f"address:{address}")


def cleanup_test_workspace() -> None:
    clients = get_clients_on_workspace(TEST_WORKSPACE)
    for c in clients:
        hyprctl("dispatch", "closewindow", f"address:{c['address']}")
    time.sleep(SETTLE_TIME)
    remaining = get_clients_on_workspace(TEST_WORKSPACE)
    if remaining:
        for c in remaining:
            hyprctl("dispatch", "closewindow", f"address:{c['address']}")
        time.sleep(SETTLE_TIME)
