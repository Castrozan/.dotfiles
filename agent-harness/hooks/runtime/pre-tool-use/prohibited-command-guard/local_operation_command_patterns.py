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

UTC_ZONE_ALIAS_PATTERN = (
    r"(?:Etc/)?(?:UTC|UCT|GMT|Universal|Zulu|Greenwich|Z)(?:0|[+-]0+)?"
)
DATE_PARSED_INPUT_ABSENT_LOOKAHEAD = (
    r"(?![^;&|\n]*\s(?:-(?-i:[A-Za-z]{0,2}[dfjrs])\b|--(?:date|file|reference|set)\b))"
)
DATE_UTC_CLOCK_READ_BY_FLAG_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}(?P<date_utc_clock_read>date)"
    rf"(?=(?:\s+[^\s;&|]+)*?\s+(?:-u|--utc|--universal)"
    rf"{COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD}){DATE_PARSED_INPUT_ABSENT_LOOKAHEAD}"
)
DATE_UTC_CLOCK_READ_BY_ZONE_PATTERN = (
    r"(?:^|[\n;&|(`{!]|\$\(|&&|\|\||\b(?:sudo|exec|env|command)\s+)\s*"
    r"(?:[A-Za-z_]\w*=\S*\s+)*"
    rf"(?P<date_utc_clock_read>TZ=[\"']?{UTC_ZONE_ALIAS_PATTERN}[\"']?"
    rf"\s+(?:[A-Za-z_]\w*=\S*\s+)*date){COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD}"
    rf"{DATE_PARSED_INPUT_ABSENT_LOOKAHEAD}"
)
DATE_UTC_CLOCK_READ_DENIAL_REASON = (
    "date -u and a TZ=UTC prefix read the clock in UTC, not the user's zone. Use "
    "plain date, which prints the local zone; 'local-time --iso' for an API "
    "parameter; and 'local-time <stamp>' to convert a stamp ending in Z before "
    "quoting it."
)

LOCAL_OPERATION_BASH_COMMAND_PATTERNS = [
    (
        DATE_INPUT_WITH_IANA_TIMEZONE_PATTERN,
        DATE_INPUT_WITH_IANA_TIMEZONE_DENIAL_REASON,
        None,
        "date_with_inline_iana_timezone",
    ),
    (
        DATE_UTC_CLOCK_READ_BY_FLAG_PATTERN,
        DATE_UTC_CLOCK_READ_DENIAL_REASON,
        None,
        "date_utc_clock_read",
    ),
    (
        DATE_UTC_CLOCK_READ_BY_ZONE_PATTERN,
        DATE_UTC_CLOCK_READ_DENIAL_REASON,
        None,
        "date_utc_clock_read",
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
        "herdr agent start splits the focused tab unless --tab pins one. For "
        "same-goal delegation, pin --tab with --no-focus and read the orchestrate "
        "skill; for unrelated work, open a fresh tab and read the herdr skill.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}herdr\s+agent\s+start\b"
        rf"(?:(?![;&|\n]).)*?\s--\s+"
        rf"(?!(?:[\"']?\$?SHELL[\"']?|/run/current-system/sw/bin/bash)\s+-lic\b)",
        "herdr agent start must launch through the login-interactive $SHELL "
        "adapter from the orchestrate skill. A direct argv launch inherits the "
        "Herdr server service PATH instead of the user's normal shell PATH.",
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
