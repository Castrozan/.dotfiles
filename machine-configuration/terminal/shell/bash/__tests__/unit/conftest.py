import os
import sys

import pytest


@pytest.fixture
def launcher_environment(tmp_path):
    executable_directory = tmp_path / "bin"
    executable_directory.mkdir()
    history_file = tmp_path / "history"
    history_file.touch()
    driver = executable_directory / "command-history-ranker"
    driver.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['HSTR_ARGUMENT_FILE']).write_text('\\n'.join(sys.argv[1:]))\n"
        "Path(os.environ['HSTR_CONFIGURATION_FILE']).write_text(os.environ['HSTR_CONFIG'])\n"
        "for command in json.loads(os.environ['HSTR_RESULTS']):\n"
        "    sys.stdout.buffer.write(command.encode() + b'\\0')\n"
        "sys.exit(int(os.environ.get('HSTR_EXIT_STATUS', '0')))\n"
    )
    driver.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        PATH=f"{executable_directory}:{environment['PATH']}",
        BASH_ENV="",
        HISTFILE=str(history_file),
        HSTR_ARGUMENT_FILE=str(tmp_path / "arguments"),
        HSTR_CONFIGURATION_FILE=str(tmp_path / "configuration"),
        HSTR_RESULTS="[]",
    )
    return environment
