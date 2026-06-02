import re

KNOWN_DAEMON_OR_SERVICE_SPAWNING_COMMAND_PATTERNS = (
    r"(?<![-\w])(?:darwin-rebuild|nixos-rebuild|rebuild)(?![-\w])",
    r"(?<![-\w])home-manager\s+switch\b",
    r"(?<![-\w])systemctl\s+(?:--user\s+)?(?:start|restart|reload)\b",
    r"(?<![-\w])launchctl\s+(?:load|bootstrap|kickstart)\b",
    r"(?<![-\w])brew\s+services\s+(?:start|restart)\b",
    r"(?<![-\w])service\s+\S+\s+(?:start|restart)\b",
)


def command_starts_a_lingering_daemon_or_service(command_string):
    return any(
        re.search(pattern, command_string)
        for pattern in KNOWN_DAEMON_OR_SERVICE_SPAWNING_COMMAND_PATTERNS
    )
