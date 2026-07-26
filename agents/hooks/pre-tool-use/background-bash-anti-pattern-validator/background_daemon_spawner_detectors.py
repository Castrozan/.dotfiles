import re

COMMAND_INVOCATION_POSITION_PREFIX = (
    r"(?:^|[\n;&|(`{!]|\$\(|&&|\|\||"
    r"\b(?:sudo|exec|nohup|time|xargs|command|if|then|else|elif|do|while|until)\s+"
    r"(?:-\S+\s+)*|"
    r"\benv\s+(?:\S+=\S+\s+)+)\s*"
)

KNOWN_DAEMON_OR_SERVICE_SPAWNING_COMMAND_PATTERNS = (
    r"(?:darwin-rebuild|nixos-rebuild|rebuild)(?![-\w])",
    r"home-manager\s+switch\b",
    r"systemctl\s+(?:--user\s+)?(?:start|restart|reload)\b",
    r"launchctl\s+(?:load|bootstrap|kickstart)\b",
    r"brew\s+services\s+(?:start|restart)\b",
    r"service\s+\S+\s+(?:start|restart)\b",
)


def command_starts_a_lingering_daemon_or_service(command_string):
    return any(
        re.search(COMMAND_INVOCATION_POSITION_PREFIX + pattern, command_string)
        for pattern in KNOWN_DAEMON_OR_SERVICE_SPAWNING_COMMAND_PATTERNS
    )
