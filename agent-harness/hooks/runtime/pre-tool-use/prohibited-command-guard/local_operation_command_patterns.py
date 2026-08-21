from shell_command_invocation_position import (
    COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD,
    COMMAND_INVOCATION_POSITION_PREFIX,
)

HERDR_TARGET_ID_PATTERN = r"w[0-9A-Za-z]+(?::[tp][0-9A-Za-z]+)?"

SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL = "CLAUDE_HEADLESS_SANCTIONED=1"
IANA_TIMEZONE_PATTERN = (
    r"[A-Za-z][A-Za-z0-9._+-]+/[A-Za-z][A-Za-z0-9._+-]+"
    r"(?:/[A-Za-z][A-Za-z0-9._+-]+)?"
)
DATE_INPUT_WITH_IANA_TIMEZONE_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}"
    rf"(?P<date_with_inline_iana_timezone>date)\s+(?:[^;&|\n]*?\s)?"
    rf"(?:-d|--date)(?:=|\s+)"
    rf'(?:"[^"\n]*{IANA_TIMEZONE_PATTERN}[^"\n]*"|'
    rf"'[^'\n]*{IANA_TIMEZONE_PATTERN}[^'\n]*'|"
    rf"[^\s;&|]*{IANA_TIMEZONE_PATTERN}[^\s;&|]*)"
)
DATE_INPUT_WITH_IANA_TIMEZONE_DENIAL_REASON = (
    "date needs the timezone as a TZ=Area/Location prefix, not inside -d/--date, "
    "to avoid a silently wrong time."
)

LOCAL_OPERATION_BASH_COMMAND_PATTERNS = [
    (
        DATE_INPUT_WITH_IANA_TIMEZONE_PATTERN,
        DATE_INPUT_WITH_IANA_TIMEZONE_DENIAL_REASON,
        None,
        "date_with_inline_iana_timezone",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}git\s+add\s+"
        rf"(?:-A|--all|\.){COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD}",
        "git add needs specific files by name, not -A/--all/., to avoid staging "
        "another agent's parallel work. Read the coding skill for more information.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}(?:git|gh\s+repo)\s+clone\s+\S*castrozan[/-]?\.?dotfiles",
        "castrozan/.dotfiles must not live on disk. Use 'gh api' for remote "
        "access instead.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}direnv\s+(allow|hook|exec|reload|status|edit|deny|block|prune|version)\b",
        "Use 'devenv shell' or 'devenv shell -- command' instead of direnv. Read "
        "the devenv skill for more information.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}herdr\s+agent\s+start\b(?:(?!\s--tab(?=[\s=]))(?!\s--\s)[^;&|\n])*(?:$|[;&|\n]|\s--\s)",
        "herdr agent start splits an active tab. Open a fresh tab so the agent is "
        "alone in its own pane, or pin --tab with --no-focus for a deliberate "
        "split. Read the herdr skill for more information.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}herdr\s+(?:workspace|tab|pane)\s+close\b"
        rf"(?!\s+{HERDR_TARGET_ID_PATTERN}{COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD})",
        "A herdr workspace/tab/pane close needs a literal target id like w2F:t3 "
        "to avoid blind work drop. Read the herdr skill for more information.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}claude(?![\w-])[^;&|`)\n]*?\s(?:-p|--print)(?:[=\s'\"]|$)",
        "claude -p/--print needs the prefix "
        f"{SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL} for a sanctioned one-off; "
        "otherwise drive an interactive session. Read the herdr skill for more "
        "information.",
        SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL,
    ),
]
