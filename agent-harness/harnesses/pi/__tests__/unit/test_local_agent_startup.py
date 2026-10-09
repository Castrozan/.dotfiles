import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest


LAUNCHER_SOURCE = Path(__file__).resolve().parents[2] / "scripts" / "local-agent.sh"


@pytest.fixture
def local_agent_launcher(tmp_path):
    command_directory = tmp_path / "actor commands"
    command_directory.mkdir()
    command_source = (
        f"#!{sys.executable}\n"
        + """import json
import os
import sys
from pathlib import Path

command = Path(sys.argv[0]).name
with open(os.environ["COMMAND_RECORD"], "a") as record:
    record.write(json.dumps({"command": command, "arguments": sys.argv[1:], "coding_directory": os.environ.get("PI_CODING_AGENT_DIR"), "agent_directory": os.environ.get("PI_AGENT_DIR")}) + "\\n")
if command == "curl":
    print('{"status":"ok"}')
if command == "pi":
    print("agent-result")
sys.exit(int(os.environ.get(command.upper() + "_EXIT_STATUS", "0")))
"""
    )
    replacements = {"@profileDirectory@": str(tmp_path / "actor profile")}
    for command in ("systemctl", "curl", "pi"):
        executable = command_directory / command
        executable.write_text(command_source)
        executable.chmod(0o755)
        replacements[f"@{command}@"] = str(executable)
    replacements["@modelId@"] = "qwen3.5-4b-uncensored"
    replacements["@healthUrl@"] = "http://127.0.0.1:8081/health"
    source = LAUNCHER_SOURCE.read_text()
    for placeholder, value in replacements.items():
        source = source.replace(placeholder, shlex.quote(value))
    launcher = tmp_path / "local-agent"
    launcher.write_text(source)
    command_record = tmp_path / "commands.jsonl"
    environment = {**os.environ, "COMMAND_RECORD": str(command_record)}
    return launcher, command_record, environment


def invoke_local_agent(local_agent_launcher, **exit_statuses):
    launcher, command_record, environment = local_agent_launcher
    environment.update({key: str(value) for key, value in exit_statuses.items()})
    result = subprocess.run(
        ["bash", str(launcher), "--print", "request with spaces"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    commands = [json.loads(line) for line in command_record.read_text().splitlines()]
    return result, commands


def test_local_agent_waits_for_readiness_and_preserves_actor_output(
    local_agent_launcher,
):
    result, commands = invoke_local_agent(local_agent_launcher)

    assert result.returncode == 0
    assert result.stdout == "agent-result\n"
    assert "Cold startup can take up to 180 seconds" in result.stderr
    assert "Qwen is ready" in result.stderr
    assert "5 minutes without connections" in result.stderr
    assert [command["command"] for command in commands] == ["systemctl", "curl", "pi"]
    assert commands[0]["arguments"] == [
        "--user",
        "start",
        "local-language-model.socket",
    ]
    assert commands[1]["arguments"] == [
        "--fail",
        "--silent",
        "--show-error",
        "--max-time",
        "180",
        "http://127.0.0.1:8081/health",
    ]
    assert commands[2]["arguments"] == [
        "--offline",
        "--provider",
        "chise",
        "--model",
        "qwen3.5-4b-uncensored",
        "--thinking",
        "off",
        "--print",
        "request with spaces",
    ]
    assert commands[2]["coding_directory"].endswith("actor profile")
    assert commands[2]["agent_directory"] == commands[2]["coding_directory"]


def test_socket_start_failure_prevents_readiness_and_agent_launch(local_agent_launcher):
    result, commands = invoke_local_agent(
        local_agent_launcher, SYSTEMCTL_EXIT_STATUS=42
    )

    assert result.returncode == 42
    assert result.stdout == ""
    assert [command["command"] for command in commands] == ["systemctl"]
    assert "Qwen is ready" not in result.stderr


def test_readiness_failure_is_visible_without_launching_agent(local_agent_launcher):
    result, commands = invoke_local_agent(local_agent_launcher, CURL_EXIT_STATUS=55)

    assert result.returncode == 55
    assert result.stdout == ""
    assert "Cold startup can take up to 180 seconds" in result.stderr
    assert "Qwen is ready" not in result.stderr
    assert [command["command"] for command in commands] == ["systemctl", "curl"]
    assert "the agent was not started" in result.stderr


def test_agent_exit_status_reaches_the_actor(local_agent_launcher):
    result, commands = invoke_local_agent(local_agent_launcher, PI_EXIT_STATUS=17)

    assert result.returncode == 17
    assert commands[-1]["command"] == "pi"
