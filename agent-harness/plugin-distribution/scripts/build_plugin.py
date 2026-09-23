import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from portable_plugin import read_portable_plugin


COMMAND_TIMEOUT_SECONDS = 30


def run_dotagents(command: str, output: Path, environment: dict[str, str]) -> None:
    process = subprocess.run(
        [environment["DOTAGENTS_PLUGIN_BUILDER"], "--project", command],
        cwd=output,
        env=environment,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
    )
    diagnostic = process.stdout + process.stderr
    if process.returncode or "warn:" in diagnostic.lower():
        raise ValueError(f"dotagents {command} failed:\n{diagnostic.strip()}")


def prepare_workspace(source: Path, output: Path, name: str, targets: tuple) -> None:
    (output / ".git").mkdir()
    shutil.copytree(source, output / "input", ignore=shutil.ignore_patterns(".git"))
    (output / ".gitignore").write_text("agents.lock\n.agents/.gitignore\n")
    (output / "agents.toml").write_text(
        f"version = 1\nagents = {json.dumps(targets)}\n\n"
        f'[[plugins]]\nname = {json.dumps(name)}\nsource = "path:./input"\n'
    )


def remove_build_inputs(output: Path) -> None:
    for name in ("input", ".git"):
        shutil.rmtree(output / name)
    for name in ("agents.toml", "agents.lock", ".gitignore", ".agents/.gitignore"):
        (output / name).unlink(missing_ok=True)


def build_plugin(source: Path, output: Path, targets: tuple[str, ...]) -> None:
    source = source.resolve(strict=True)
    output = output.absolute()
    name = read_portable_plugin(source, targets)
    if output.resolve().is_relative_to(source):
        raise ValueError("Output must be outside the plugin source")
    output.mkdir()
    try:
        prepare_workspace(source, output, name, targets)
        with tempfile.TemporaryDirectory(prefix="agent-plugin-build-") as state:
            environment = os.environ | {
                "HOME": state,
                "XDG_CONFIG_HOME": state,
                "XDG_CACHE_HOME": state,
                "XDG_STATE_HOME": state,
                "NO_COLOR": "1",
            }
            run_dotagents("install", output, environment)
            run_dotagents("doctor", output, environment)
        remove_build_inputs(output)
    except BaseException:
        shutil.rmtree(output)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build native artifacts from one Agent Plugins v1 package."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", action="append", required=True)
    arguments = parser.parse_args()
    try:
        build_plugin(arguments.source, arguments.output, tuple(arguments.target))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"agent-plugin-build: {error}\n")
    print(arguments.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
