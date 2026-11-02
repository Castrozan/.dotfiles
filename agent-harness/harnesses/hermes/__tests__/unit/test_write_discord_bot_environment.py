import stat
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts/write-discord-bot-environment.py"
)


def run_writer(environment_path, token_path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(environment_path), str(token_path), "42"],
        capture_output=True,
        text=True,
    )


def test_writes_the_token_and_allowed_user_readable_only_by_the_owner(tmp_path):
    token_path = tmp_path / "token"
    token_path.write_text("secret-token\n")
    environment_path = tmp_path / "profiles/silver/.env"

    result = run_writer(environment_path, token_path)

    assert result.returncode == 0
    assert environment_path.read_text() == (
        "DISCORD_BOT_TOKEN=secret-token\nDISCORD_ALLOWED_USERS=42\n"
    )
    assert stat.S_IMODE(environment_path.stat().st_mode) == 0o600
    assert "secret-token" not in result.stdout + result.stderr


def test_replaces_an_earlier_environment_when_the_token_rotates(tmp_path):
    token_path = tmp_path / "token"
    token_path.write_text("rotated-token")
    environment_path = tmp_path / ".env"
    environment_path.write_text("DISCORD_BOT_TOKEN=old-token\n")

    assert run_writer(environment_path, token_path).returncode == 0

    assert "old-token" not in environment_path.read_text()
    assert list(tmp_path.glob("*.tmp")) == []


def test_keeps_the_values_hermes_saved_across_gateway_restarts(tmp_path):
    token_path = tmp_path / "token"
    token_path.write_text("rotated-token")
    environment_path = tmp_path / ".env"
    environment_path.write_text(
        "DISCORD_BOT_TOKEN=old-token\n"
        "DISCORD_ALLOWED_USERS=7\n"
        "DISCORD_HOME_CHANNEL=123\n"
        "DISCORD_HOME_CHANNEL_THREAD_ID=\n"
    )

    assert run_writer(environment_path, token_path).returncode == 0

    assert environment_path.read_text() == (
        "DISCORD_HOME_CHANNEL=123\n"
        "DISCORD_HOME_CHANNEL_THREAD_ID=\n"
        "DISCORD_BOT_TOKEN=rotated-token\n"
        "DISCORD_ALLOWED_USERS=42\n"
    )


def test_refuses_an_empty_token_and_keeps_the_earlier_environment(tmp_path):
    token_path = tmp_path / "token"
    token_path.write_text("\n")
    environment_path = tmp_path / ".env"
    environment_path.write_text("DISCORD_BOT_TOKEN=working-token\n")

    assert run_writer(environment_path, token_path).returncode != 0

    assert "working-token" in environment_path.read_text()
