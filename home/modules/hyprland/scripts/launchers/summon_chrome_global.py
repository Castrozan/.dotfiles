import os
import re
import subprocess
import time
from pathlib import Path

from hyprland_ipc import get_all_clients, run_hyprctl, run_hyprctl_json

CHROME_GLOBAL_CLASS = "chrome-global"
CHROME_GLOBAL_DATA_DIR = Path.home() / ".config" / "chrome-global"
CHROME_GLOBAL_HYPRLAND_TAG = "chrome-global-main-window"
CHROME_GLOBAL_TITLE_FALLBACK_PATTERN = re.compile(r"Chat|agenda|ᓚᘏᗢ", re.IGNORECASE)
CHROME_GLOBAL_FLAGS = [
    f"--user-data-dir={CHROME_GLOBAL_DATA_DIR}",
    f"--class={CHROME_GLOBAL_CLASS}",
    "--enable-features=UseNativeNotifications",
]
CHROME_GLOBAL_URLS = [
    "chrome://newtab",
    "https://mail.google.com/chat/u/0/#chat/home",
    "https://desenv.betha.com.br/secure/RapidBoard.jspa?rapidView=514&selectedIssue=AP-9448",
    "https://gitlab.services.betha.cloud/",
    "chrome://newtab",
]

CHROME_GLOBAL_PREFERENCES_JSON = """\
{
  "session": {
    "restore_on_startup": 1
  },
  "browser": {
    "has_seen_welcome_page": true
  }
}
"""


def find_clients_by_class(window_class: str) -> list[dict]:
    return [c for c in get_all_clients() if c.get("class") == window_class]


def find_chrome_global_window_by_hyprland_tag() -> dict | None:
    for client in find_clients_by_class(CHROME_GLOBAL_CLASS):
        tags = client.get("tags", [])
        if CHROME_GLOBAL_HYPRLAND_TAG in tags:
            return client
    return None


def find_chrome_global_window_by_title_pattern() -> dict | None:
    for client in find_clients_by_class(CHROME_GLOBAL_CLASS):
        if client.get("floating"):
            continue
        title = client.get("title", "")
        if CHROME_GLOBAL_TITLE_FALLBACK_PATTERN.search(title):
            return client
    return None


def find_chrome_global_window_by_initial_title_pattern() -> dict | None:
    for client in find_clients_by_class(CHROME_GLOBAL_CLASS):
        if client.get("floating"):
            continue
        initial_title = client.get("initialTitle", "")
        if CHROME_GLOBAL_TITLE_FALLBACK_PATTERN.search(initial_title):
            return client
    return None


def tag_window_as_chrome_global_main(window_address: str) -> None:
    run_hyprctl(
        "dispatch",
        "tagwindow",
        f"+{CHROME_GLOBAL_HYPRLAND_TAG}",
        f"address:{window_address}",
    )


def find_chrome_global_main_window() -> dict | None:
    client = find_chrome_global_window_by_hyprland_tag()
    if client:
        return client

    client = find_chrome_global_window_by_title_pattern()
    if client:
        tag_window_as_chrome_global_main(client["address"])
        return client

    client = find_chrome_global_window_by_initial_title_pattern()
    if client:
        tag_window_as_chrome_global_main(client["address"])
        return client

    return None


def get_active_workspace_id_via_activeworkspace() -> int | None:
    workspace = run_hyprctl_json("activeworkspace")
    if not workspace:
        return None
    return workspace.get("id")


def chrome_global_has_never_been_launched() -> bool:
    return not (CHROME_GLOBAL_DATA_DIR / ".initialized").exists()


def initialize_chrome_global_profile_if_needed() -> None:
    default_dir = CHROME_GLOBAL_DATA_DIR / "Default"
    if default_dir.is_dir():
        return

    default_dir.mkdir(parents=True, exist_ok=True)
    preferences = default_dir / "Preferences"
    preferences.write_text(CHROME_GLOBAL_PREFERENCES_JSON)


def wait_for_chrome_global_window_and_tag_it() -> None:
    max_attempts = 50
    for _ in range(max_attempts):
        for client in find_clients_by_class(CHROME_GLOBAL_CLASS):
            tag_window_as_chrome_global_main(client["address"])
            return
        time.sleep(0.1)


def launch_chrome_global() -> None:
    initialize_chrome_global_profile_if_needed()

    if chrome_global_has_never_been_launched():
        (CHROME_GLOBAL_DATA_DIR / ".initialized").touch()
        subprocess.Popen(
            ["google-chrome-stable", *CHROME_GLOBAL_FLAGS, *CHROME_GLOBAL_URLS]
        )
        wait_for_chrome_global_window_and_tag_it()
        return

    os.execvp(
        "google-chrome-stable",
        ["google-chrome-stable", *CHROME_GLOBAL_FLAGS],
    )


def summon_or_launch_chrome_global() -> None:
    current_workspace_id = get_active_workspace_id_via_activeworkspace()
    client = find_chrome_global_main_window()

    if client is None:
        launch_chrome_global()
        return

    window_address = client["address"]
    window_workspace_id = client["workspace"]["id"]

    if window_workspace_id == current_workspace_id:
        run_hyprctl("dispatch", "focuswindow", f"address:{window_address}")
        return

    subprocess.run(
        [
            "hypr-detach-from-group-and-move-to-workspace",
            "follow",
            str(current_workspace_id),
            window_address,
        ]
    )


def main() -> None:
    summon_or_launch_chrome_global()


if __name__ == "__main__":
    main()
