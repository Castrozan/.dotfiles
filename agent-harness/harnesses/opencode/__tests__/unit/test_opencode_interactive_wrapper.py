import json
import os
import subprocess
from pathlib import Path

import pytest


LAUNCHER = Path(__file__).resolve().parents[2] / "scripts/launch_opencode.sh"


@pytest.mark.parametrize(
    ("arguments", "interactive"),
    [
        ([], True),
        (["--server", "http://localhost:9000"], True),
        (["--standalone"], True),
        (["/workspace"], True),
        (["mini", "--continue"], True),
        (["run", "hello"], False),
        (["api", "get", "/api/agent"], False),
        (["service", "status"], False),
        (["--help"], False),
        (["-h"], False),
        (["--version"], False),
        (["-v"], False),
    ],
)
def test_launcher_isolates_interactive_configuration(tmp_path, arguments, interactive):
    executable = tmp_path / "bin/opencode"
    executable.parent.mkdir()
    executable.write_text(
        "#!/usr/bin/env python3\nimport os,json,sys\n"
        'print(json.dumps({"args":sys.argv[1:],"config":os.getenv("OPENCODE_CONFIG"),"preferences":os.getenv("AGENT_INTERACTIVE_PREFERENCES_PATH")}))\n'
    )
    executable.chmod(0o755)
    source = LAUNCHER.read_text()
    for key, value in {
        "interactiveSessionConfigOverlay": "/interactive.json",
        "interactivePreferencesFile": "/interactive.md",
        "opencodeAuthenticated": str(tmp_path),
    }.items():
        source = source.replace(f"@{key}@", value)
    launcher = tmp_path / "launch.sh"
    launcher.write_text(source)
    environment = {
        key: value
        for key, value in os.environ.items()
        if key != "AGENT_INTERACTIVE_PREFERENCES_PATH"
    }
    environment["OPENCODE_CONFIG"] = "/autonomous.json"
    result = subprocess.run(
        ["bash", str(launcher), *arguments],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    actual = json.loads(result.stdout)
    assert actual["args"] == arguments
    assert actual["config"] == (
        "/interactive.json" if interactive else "/autonomous.json"
    )
    assert actual["preferences"] == ("/interactive.md" if interactive else None)


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ([], ["--standalone"]),
        (["--continue"], ["--standalone", "--continue"]),
        (["run", "hello"], ["run", "--standalone", "hello"]),
        (["mini", "--continue"], ["mini", "--standalone", "--continue"]),
        (["serve", "--port", "0"], ["serve", "--port", "0"]),
        (["--server", "http://localhost:9000"], ["--server", "http://localhost:9000"]),
        (["run", "--standalone", "hello"], ["run", "--standalone", "hello"]),
    ],
)
def test_authenticated_launcher_preserves_configuration_isolation(
    tmp_path, arguments, expected
):
    executable = tmp_path / "bin/opencode"
    executable.parent.mkdir()
    executable.write_text(
        "#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n"
    )
    executable.chmod(0o755)
    source = (
        (LAUNCHER.parent / "launch_authenticated_opencode.sh")
        .read_text()
        .replace("@opencodeApiKeyFile@", str(tmp_path / "absent-key"))
        .replace("@opencodeUnwrapped@", str(tmp_path))
    )
    launcher = tmp_path / "authenticated.sh"
    launcher.write_text(source)
    result = subprocess.run(
        ["bash", str(launcher), *arguments], capture_output=True, text=True, check=True
    )
    assert json.loads(result.stdout) == expected
