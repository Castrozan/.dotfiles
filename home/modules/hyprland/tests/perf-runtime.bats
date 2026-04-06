#!/usr/bin/env bats

setup() {
    if [ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
        skip "no Hyprland session running"
    fi
}

_measure_ms() {
    local start end
    start=$(date +%s%N)
    "$@" >/dev/null 2>&1
    end=$(date +%s%N)
    echo $(( (end - start) / 1000000 ))
}

_qs_bar_ipc() {
    qs -p ~/.dotfiles/.config/quickshell/bar ipc call "$@"
}

# ── Hyprland IPC ──────────────────────────────────────────────────────────────

@test "perf: hyprctl version < 100ms" {
    ms=$(_measure_ms hyprctl version)
    echo "# hyprctl version: ${ms}ms" >&3
    [ "$ms" -lt 100 ]
}

@test "perf: hyprctl clients -j < 100ms" {
    ms=$(_measure_ms hyprctl clients -j)
    echo "# hyprctl clients: ${ms}ms" >&3
    [ "$ms" -lt 100 ]
}

@test "perf: hyprctl activeworkspace -j < 100ms" {
    ms=$(_measure_ms hyprctl activeworkspace -j)
    echo "# hyprctl activeworkspace: ${ms}ms" >&3
    [ "$ms" -lt 100 ]
}

# ── Workspace switch ───────────���─────────────────────────────────────────────

@test "perf: workspace switch < 150ms" {
    local current target
    current=$(hyprctl activeworkspace -j | jq '.id')
    target=$((current < 10 ? current + 1 : current - 1))

    ms=$(_measure_ms hyprctl dispatch workspace "$target")
    hyprctl dispatch workspace "$current" >/dev/null 2>&1

    echo "# workspace switch: ${ms}ms" >&3
    [ "$ms" -lt 150 ]
}

# ── QuickShell IPC (window switcher) ─────────────────────────────────────────

@test "perf: window switcher open < 300ms" {
    ms=$(_measure_ms qs -c switcher ipc call switcher open)
    qs -c switcher ipc call switcher cancel >/dev/null 2>&1
    sleep 0.1

    echo "# window switcher open: ${ms}ms" >&3
    [ "$ms" -lt 300 ]
}

# ── QuickShell IPC (launcher) ──────────��─────────────────────────────────────

@test "perf: launcher toggle < 300ms" {
    ms=$(_measure_ms _qs_bar_ipc launcher toggle)
    sleep 0.15
    _qs_bar_ipc launcher toggle >/dev/null 2>&1

    echo "# launcher toggle: ${ms}ms" >&3
    [ "$ms" -lt 300 ]
}

# ─��� QuickShell IPC (dashboard) ───────────────────────────────────────────────

@test "perf: dashboard toggle < 300ms" {
    ms=$(_measure_ms _qs_bar_ipc dashboard toggle)
    sleep 0.15
    _qs_bar_ipc dashboard toggle >/dev/null 2>&1

    echo "# dashboard toggle: ${ms}ms" >&3
    [ "$ms" -lt 300 ]
}

# ── QuickShell IPC (sidebar/notifications) ───────────────────────────────────

@test "perf: sidebar toggle < 300ms" {
    ms=$(_measure_ms _qs_bar_ipc sidebar toggle)
    sleep 0.15
    _qs_bar_ipc sidebar toggle >/dev/null 2>&1

    echo "# sidebar toggle: ${ms}ms" >&3
    [ "$ms" -lt 300 ]
}

# ── QuickShell IPC (workspace overview) ──────────────────────────────────────

@test "perf: workspace overview toggle < 300ms" {
    ms=$(_measure_ms qs -c overview ipc call overview toggle)
    sleep 0.15
    qs -c overview ipc call overview toggle >/dev/null 2>&1

    echo "# workspace overview: ${ms}ms" >&3
    [ "$ms" -lt 300 ]
}

# ── Audio ───────────��────────────────────────────────────────────────────────

@test "perf: volume control < 500ms" {
    if ! command -v volume &>/dev/null; then
        skip "volume not installed"
    fi

    ms=$(_measure_ms volume --inc)
    volume --dec >/dev/null 2>&1

    echo "# volume control: ${ms}ms" >&3
    [ "$ms" -lt 500 ]
}

# ── Terminal ────���────────────────────────��───────────────────────────────────

@test "perf: fish interactive startup < 500ms" {
    ms=$(_measure_ms fish -i -c exit)
    echo "# fish startup: ${ms}ms" >&3
    [ "$ms" -lt 500 ]
}

# ── Tmux ───��─────────────────────────────────���───────────────────────────────

@test "perf: tmux new session < 500ms" {
    ms=$(_measure_ms tmux new-session -d -s _bats_perf_test)
    tmux kill-session -t _bats_perf_test >/dev/null 2>&1

    echo "# tmux new session: ${ms}ms" >&3
    [ "$ms" -lt 500 ]
}

@test "perf: tmux split window < 300ms" {
    tmux new-session -d -s _bats_perf_split >/dev/null 2>&1

    ms=$(_measure_ms tmux split-window -t _bats_perf_split)
    tmux kill-session -t _bats_perf_split >/dev/null 2>&1

    echo "# tmux split: ${ms}ms" >&3
    [ "$ms" -lt 300 ]
}
