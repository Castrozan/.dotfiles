import os
import sys
from pathlib import Path


DECLARED_ENVIRONMENT_KEYS = ("DISCORD_BOT_TOKEN", "DISCORD_ALLOWED_USERS")


def render_discord_bot_environment(
    existing_environment: str, bot_token: str, allowed_discord_user_id: str
) -> str:
    runtime_saved_lines = [
        line
        for line in existing_environment.splitlines()
        if line.partition("=")[0] not in DECLARED_ENVIRONMENT_KEYS
    ]
    declared_lines = [
        f"DISCORD_BOT_TOKEN={bot_token}",
        f"DISCORD_ALLOWED_USERS={allowed_discord_user_id}",
    ]
    return "\n".join(runtime_saved_lines + declared_lines) + "\n"


def write_private_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    descriptor = os.open(temporary_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as temporary_file:
        temporary_file.write(content)
    os.replace(temporary_path, path)


def main() -> None:
    environment_path, token_path, allowed_discord_user_id = sys.argv[1:]
    bot_token = Path(token_path).read_text().strip()
    if not bot_token:
        sys.exit(f"Discord bot token is empty: {token_path}")
    environment_file = Path(environment_path)
    existing_environment = (
        environment_file.read_text() if environment_file.exists() else ""
    )
    write_private_file(
        environment_file,
        render_discord_bot_environment(
            existing_environment, bot_token, allowed_discord_user_id
        ),
    )


if __name__ == "__main__":
    main()
