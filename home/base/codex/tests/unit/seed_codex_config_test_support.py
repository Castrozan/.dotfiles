import os
import subprocess
import sys
import tomllib
from pathlib import Path


SCRIPT_UNDER_TEST = (
    Path(__file__).parents[2] / "config" / "seed_codex_config_mutable.py"
)


def run_seed(tmp_path, environment_overrides=None):
    environment = os.environ.copy()
    environment["HOME"] = str(tmp_path)
    if environment_overrides is not None:
        environment.update(environment_overrides)
    return subprocess.run(
        [sys.executable, str(SCRIPT_UNDER_TEST)],
        check=False,
        env=environment,
        capture_output=True,
        text=True,
    )


def read_live_config(tmp_path):
    with (tmp_path / ".codex" / "config.toml").open("rb") as stream:
        return tomllib.load(stream)
