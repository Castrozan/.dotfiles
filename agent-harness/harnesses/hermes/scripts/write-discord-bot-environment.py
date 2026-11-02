import os
import sys
from pathlib import Path


def render_discord_bot_environment(bot_token: str, allowed_discord_user_id: str) -> str:
    return (
        f"DISCORD_BOT_TOKEN={bot_token}\n"
        f"DISCORD_ALLOWED_USERS={allowed_discord_user_id}\n"
    )


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
    write_private_file(
        Path(environment_path),
        render_discord_bot_environment(bot_token, allowed_discord_user_id),
    )


if __name__ == "__main__":
    main()
