from __future__ import annotations

import re

UNKNOWN_WAIT_TARGET = "unknown"

WAIT_TARGET_PATTERNS_IN_PRIORITY_ORDER = (
    ("background-task-output", r"/tasks/[\w-]+\.output\b"),
    (
        "ci-run",
        r"\bgh\s+(?:run\s|pr\s+checks\b)|\bglab\s+(?:ci|pipeline)\b"
        r"|/pipelines\b|/actions/runs\b|\bci-watcher\b",
    ),
    (
        "peer-agent",
        r"\borchestrator\s+(?:heartbeat\s+show|status)\b|\bherdr\s+agent\s+(?:read|get|list|wait)\b"
        r"|\ba2a\s+(?:status|inbox|list)\b",
    ),
    ("pane-output", r"\bherdr\s+pane\s+(?:read|get|list)\b|\btmux\s+capture-pane\b"),
    (
        "process-exit",
        r"\bpgrep\b|\bkill\s+-0\b|\bps\s+(?:-p|aux|-ef)\b|\bpidof\b|/proc/",
    ),
    (
        "service-state",
        r"\bsystemctl\b|\blaunchctl\b|\bjournalctl\b|\bdocker\s+(?:ps|inspect)\b",
    ),
    ("desktop-window", r"\bhypr(?:ctl|use)\b|\bgrim\b|\bxdotool\b|\bwmctrl\b"),
    ("browser-page", r"\bchrome-devtools\b|\bshorts-browser\b"),
    (
        "local-endpoint",
        r"\blocalhost\b|\b127\.0\.0\.1\b|\b0\.0\.0\.0\b|\[::1\]"
        r"|\bss\s+-\w*l|\bnc\s+-\w*z\b|\blsof\s+-i\b",
    ),
    (
        "file-content",
        r"(?:^|\|\||[;&({\n!]|\b(?:until|while|if|do|then)\s)\s*(?:grep|rg)\s+"
        r"(?:-\w*[qc]|--quiet|--count)|(?:\[|\btest)\s+(?:!\s+)?-[efsd]\s"
        r"|\btail\s+-(?:n\s*)?\d|\bwc\s+-[lc]\b|\bstat\s",
    ),
    (
        "forge-merge-request",
        r"\bgh\s+(?:pr\s+view|api)\b|\bglab\s+(?:mr|api)\b|merge_requests|/pulls/",
    ),
    ("remote-endpoint", r"\b(?:curl|wget|websocat)\b"),
)

COMPILED_WAIT_TARGET_PATTERNS = tuple(
    (target_name, re.compile(pattern))
    for target_name, pattern in WAIT_TARGET_PATTERNS_IN_PRIORITY_ORDER
)

TARGETS_WITHOUT_AN_EVENT_SOURCE = frozenset({"forge-merge-request", "remote-endpoint"})

EVENT_REPLACEMENT_BY_WAIT_TARGET = {
    "background-task-output": (
        "the harness notifies you when that background task ends; do other work or "
        "end the turn instead of reading its output file."
    ),
    "ci-run": (
        "run `ci-watcher <run-id>`, backgrounded where the harness can, and act on "
        "its exit code."
    ),
    "peer-agent": (
        "`herdr agent wait <pane> --until done --until blocked --timeout <ms>`, "
        "`orchestrator watch` under Monitor or `a2a ask`; read `orchestrator status` "
        "once when its state is due."
    ),
    "pane-output": (
        "`herdr pane wait-output <pane> --match <text> --timeout <ms>` returns the "
        "moment the text appears."
    ),
    "process-exit": (
        "background the command itself and take its completion notification, or "
        "block on `wait-for-event process <pid>`."
    ),
    "service-state": (
        "`systemctl start` returns once a notify or oneshot unit is up; "
        "`wait-for-event process <MainPID>` or `docker wait <name>` when it ends."
    ),
    "desktop-window": (
        "`hypruse wait_for window_open --match <title> --timeout <s>` blocks on the "
        "compositor event; `title_change` and `layer_open` work the same way."
    ),
    "browser-page": (
        "`chrome-devtools navigate_page` already returns on load; for later content, "
        "`evaluate_script` a promise that a MutationObserver resolves."
    ),
    "local-endpoint": (
        "`wait-for-event file <server log> --match '<ready line>'`, or `curl --retry "
        "30 --retry-connrefused --retry-delay 1 <url>` when the server logs nothing."
    ),
    "file-content": (
        "`wait-for-event file <path> --match <regex>` returns on the first matching "
        "line; if your own command writes it, background that command instead."
    ),
    "forge-merge-request": (
        "`ci-watcher <pipeline-id>` for its pipeline, then read the state once; a "
        "capped loop runs only backgrounded or under Monitor, as a safety net."
    ),
    "remote-endpoint": (
        "read it once when the result is due; nothing pushes it here, so a capped "
        "loop runs only backgrounded or under Monitor, as a safety net."
    ),
    UNKNOWN_WAIT_TARGET: (
        "background the command that causes the change and take its notification, "
        "or block on `wait-for-event file` or `wait-for-event process`."
    ),
}


def waited_target(command_text):
    for target_name, pattern in COMPILED_WAIT_TARGET_PATTERNS:
        if pattern.search(command_text):
            return target_name
    return UNKNOWN_WAIT_TARGET


def target_has_an_event_source(target_name):
    return target_name not in TARGETS_WITHOUT_AN_EVENT_SOURCE
