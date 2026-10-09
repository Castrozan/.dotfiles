import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tomllib

import pytest


pytestmark = pytest.mark.skipif(
    shutil.which("shellcheck") is None, reason="Native ShellCheck is unavailable"
)


def run_shellcheck_driver(directory, inputs):
    configuration = Path(__file__).resolve().parents[6] / ".qlty/qlty.toml"
    settings = tomllib.loads(configuration.read_text())
    script = settings["plugins"]["definitions"]["native-shellcheck"]["drivers"]["lint"][
        "script"
    ]
    command = shlex.split(script.replace("${target}", shlex.join(map(str, inputs))))
    completed = subprocess.run(
        command, cwd=directory, capture_output=True, text=True, timeout=10
    )
    return completed.returncode, json.loads(completed.stdout)


def sourced_script(directory):
    directory.mkdir()
    main = directory / "main.sh"
    library = directory / "library.sh"
    main.write_text(
        '#!/usr/bin/env bash\nreadonly PROJECT_PREFIX="example"\n'
        'readonly APP_NAME="Example"\nsource library.sh\n'
    )
    library.write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "$PROJECT_PREFIX" "$APP_NAME"\n'
    )
    return main, library


def test_sourced_variable_usage_is_independent_of_input_batch(tmp_path):
    main, library = sourced_script(tmp_path / "scripts")
    single = run_shellcheck_driver(main.parent, [main])
    batched = run_shellcheck_driver(main.parent, [main, library])
    assert single == batched == (0, [])


def test_source_paths_resolve_from_the_script_directory(tmp_path):
    main, _ = sourced_script(tmp_path / "scripts")
    assert run_shellcheck_driver(tmp_path, [main]) == (0, [])


def test_source_following_preserves_unused_variable_findings(tmp_path):
    main, _ = sourced_script(tmp_path / "scripts")
    main.write_text(main.read_text() + 'readonly unused_configuration="unused"\n')
    status, diagnostics = run_shellcheck_driver(tmp_path, [main])
    assert status == 1
    assert [entry["code"] for entry in diagnostics] == [2034]


def test_missing_sourced_files_still_fail(tmp_path):
    main, library = sourced_script(tmp_path / "scripts")
    library.unlink()
    status, diagnostics = run_shellcheck_driver(tmp_path, [main])
    assert status == 1
    assert 1091 in {entry["code"] for entry in diagnostics}


def test_malformed_sourced_files_still_fail(tmp_path):
    main, library = sourced_script(tmp_path / "scripts")
    library.write_text("if; then\n")
    status, diagnostics = run_shellcheck_driver(tmp_path, [main])
    assert status == 1
    assert 1094 in {entry["code"] for entry in diagnostics}
