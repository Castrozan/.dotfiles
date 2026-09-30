import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import codex_client_launch


@pytest.mark.parametrize("command", ["exec", "--"])
@pytest.mark.parametrize("endpoint", ["/trusted.sock", None])
def test_native_exec_preserves_literal_arguments_without_shell_evaluation(
    tmp_path, command, endpoint
):
    binary = tmp_path / "codex"
    binary.write_text(
        f"#!{sys.executable}\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n"
    )
    binary.chmod(0o700)
    sentinel = tmp_path / "must-not-exist"
    prompt = f"literal argument; $(touch {sentinel})"
    arguments = [command, prompt]
    directory = str(Path(codex_client_launch.__file__).parent)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, {directory!r}); "
            "import codex_client_launch; "
            f"codex_client_launch.register_client = lambda *args: {endpoint!r}; "
            "codex_client_launch.main()",
            *arguments,
        ],
        env={**os.environ, "CODEX_LAUNCHER_BINARY": str(binary)},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    expected = (
        arguments
        if command == "exec"
        else ["--remote", "unix:///trusted.sock", *arguments]
        if endpoint
        else ["--no-daemon", *arguments]
    )
    assert json.loads(result.stdout) == expected
    assert not sentinel.exists()
