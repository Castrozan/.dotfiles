import os

import desktop_benchmarks.hyprland
import desktop_benchmarks.terminal


def is_hyprland_running() -> bool:
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))


BENCHMARKS_HYPRLAND = [
    ("hyprctl-ipc", desktop_benchmarks.hyprland.bench_hyprctl_ipc),
    ("hyprctl-clients", desktop_benchmarks.hyprland.bench_hyprctl_clients),
    ("workspace-switch", desktop_benchmarks.hyprland.bench_workspace_switch),
    ("window-switcher", desktop_benchmarks.hyprland.bench_window_switcher),
    ("launcher-qs", desktop_benchmarks.hyprland.bench_launcher_qs),
    ("dashboard", desktop_benchmarks.hyprland.bench_dashboard),
    ("sidebar", desktop_benchmarks.hyprland.bench_sidebar),
    ("workspace-overview", desktop_benchmarks.hyprland.bench_workspace_overview),
    ("volume-control", desktop_benchmarks.hyprland.bench_volume_control),
    ("fuzzel", desktop_benchmarks.hyprland.bench_fuzzel_launch),
]


BENCHMARKS_TERMINAL = [
    ("wezterm-launch", desktop_benchmarks.terminal.bench_wezterm_launch),
    ("tmux-new-session", desktop_benchmarks.terminal.bench_tmux_new_session),
    ("tmux-split-window", desktop_benchmarks.terminal.bench_tmux_split),
]


ALL_BENCHMARKS = BENCHMARKS_HYPRLAND + BENCHMARKS_TERMINAL


def get_available_benchmarks() -> list[tuple[str, object]]:
    if is_hyprland_running():
        return ALL_BENCHMARKS
    return BENCHMARKS_TERMINAL
