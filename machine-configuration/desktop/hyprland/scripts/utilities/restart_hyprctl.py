import subprocess

from hyprland_runtime import ensure_hyprctl_connected
from hyprland_theme import apply_theme_border_colors_from_config

SCREENCOPY_SERVICES: list[str] = []


def stop_active_screencopy_services() -> list[str]:
    stopped = []
    for service in SCREENCOPY_SERVICES:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", service],
            capture_output=True,
        )
        if result.returncode == 0:
            subprocess.run(
                ["systemctl", "--user", "stop", service],
                capture_output=True,
            )
            stopped.append(service)
    return stopped


def restart_previously_stopped_services(
    stopped_services: list[str],
) -> None:
    if not stopped_services:
        return
    import time

    time.sleep(0.5)
    for service in stopped_services:
        subprocess.run(
            ["systemctl", "--user", "start", service],
            capture_output=True,
        )


def reload_hyprland_config_only_with_screencopy_services_paused() -> None:
    stopped = stop_active_screencopy_services()
    if stopped:
        import time

        time.sleep(0.3)
    subprocess.run(["hyprctl", "reload", "config-only"])
    restart_previously_stopped_services(stopped)


def main() -> None:
    if not ensure_hyprctl_connected():
        return
    reload_hyprland_config_only_with_screencopy_services_paused()
    apply_theme_border_colors_from_config()


if __name__ == "__main__":
    main()
