import json
import subprocess
import sys


COMMAND_TIMEOUT_SECONDS = 2
WEZTERM_CLASSES = frozenset({"org.wezfurlong.wezterm", "wezterm"})
HAMMERSPOON_WEZTERM_SUMMON_EXPRESSION = "summonWezTermToCurrentWorkspace()"


def string_value(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def run_json_command(arguments: list[str]) -> object | None:
    try:
        result = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def wezterm_focus_order(client: dict[str, object]) -> int:
    focus_history_identifier = client.get("focusHistoryID")
    if isinstance(focus_history_identifier, int) and focus_history_identifier >= 0:
        return focus_history_identifier
    return sys.maxsize


def current_workspace_wezterm_address(hyprctl_path: str) -> str:
    if not hyprctl_path:
        return ""
    active_workspace = run_json_command([hyprctl_path, "-j", "activeworkspace"])
    clients = run_json_command([hyprctl_path, "-j", "clients"])
    if not isinstance(active_workspace, dict) or not isinstance(clients, list):
        return ""
    active_workspace_identifier = active_workspace.get("id")
    matching_clients = []
    for client in clients:
        if not isinstance(client, dict):
            continue
        workspace = client.get("workspace")
        application_class = string_value(client.get("class")).lower()
        if (
            not isinstance(workspace, dict)
            or workspace.get("id") != active_workspace_identifier
            or application_class not in WEZTERM_CLASSES
            or client.get("mapped") is not True
            or client.get("hidden") is True
        ):
            continue
        matching_clients.append(client)
    if not matching_clients:
        return ""
    matching_clients.sort(key=wezterm_focus_order)
    return string_value(matching_clients[0].get("address"))


def focus_current_hyprland_workspace_wezterm(hyprctl_path: str) -> bool:
    wezterm_address = current_workspace_wezterm_address(hyprctl_path)
    if not wezterm_address:
        return False
    try:
        result = subprocess.run(
            [
                hyprctl_path,
                "dispatch",
                "focuswindow",
                f"address:{wezterm_address}",
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def summon_wezterm_to_current_darwin_workspace(hammerspoon_path: str) -> bool:
    if not hammerspoon_path:
        return False
    try:
        result = subprocess.run(
            [
                hammerspoon_path,
                "-c",
                HAMMERSPOON_WEZTERM_SUMMON_EXPRESSION,
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def focus_workspace_wezterm(platform: str, desktop_focus_path: str) -> bool:
    if platform == "linux":
        return focus_current_hyprland_workspace_wezterm(desktop_focus_path)
    if platform == "darwin":
        return summon_wezterm_to_current_darwin_workspace(desktop_focus_path)
    return False


def herdr_pane_for_thread(herdr_path: str, thread_identifier: str) -> str:
    if not herdr_path or not thread_identifier:
        return ""
    agent_list = run_json_command([herdr_path, "agent", "list"])
    if not isinstance(agent_list, dict):
        return ""
    result = agent_list.get("result")
    agents = result.get("agents") if isinstance(result, dict) else None
    if not isinstance(agents, list):
        return ""
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        agent_session = agent.get("agent_session")
        if (
            isinstance(agent_session, dict)
            and agent_session.get("value") == thread_identifier
        ):
            return string_value(agent.get("pane_id"))
    return ""


def focus_herdr_agent(herdr_path: str, pane_identifier: str) -> None:
    if not pane_identifier:
        return
    try:
        subprocess.run(
            [herdr_path, "agent", "focus", pane_identifier],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def handle_notification_action(
    action: str,
    platform: str,
    desktop_focus_path: str,
    herdr_path: str,
    thread_identifier: str,
) -> None:
    linux_action_requests_focus = platform == "linux" and action == "default"
    darwin_action_requests_focus = platform == "darwin" and action in {
        "@ACTIONCLICKED",
        "@CONTENTCLICKED",
        "Focus session",
    }
    if not linux_action_requests_focus and not darwin_action_requests_focus:
        return
    focus_session(platform, desktop_focus_path, herdr_path, thread_identifier)


def focus_session(
    platform: str,
    desktop_focus_path: str,
    herdr_path: str,
    thread_identifier: str,
) -> None:
    pane_identifier = herdr_pane_for_thread(herdr_path, thread_identifier)
    if not pane_identifier or not focus_workspace_wezterm(platform, desktop_focus_path):
        return
    focus_herdr_agent(herdr_path, pane_identifier)
