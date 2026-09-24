import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from itertools import chain
from pathlib import Path

from claude_mcp import write_claude_mcp
from opencode_mcp import write_opencode_mcp
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
    if process.returncode and command != "doctor":
        raise ValueError(f"dotagents {command} failed:\n{diagnostic.strip()}")
    if process.returncode or "warn:" in diagnostic.lower():
        (output / f"dotagents-{command}.log").write_text(diagnostic)
        print(diagnostic.strip(), file=sys.stderr)


def copy_package(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        copied = destination / path.relative_to(source)
        if copied.is_symlink():
            copied.unlink()
    shutil.copytree(
        source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git")
    )
    for path in chain((destination,), destination.rglob("*")):
        path.chmod(path.stat().st_mode | stat.S_IWUSR)


def prepare_workspace(source: Path, output: Path, name: str, targets: tuple) -> None:
    (output / ".git").mkdir()
    copy_package(source, output / "input")
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


def deliver_package(source: Path, output: Path, name: str, targets: tuple) -> Path:
    plugin = output / ".agents/plugins" / name
    copy_package(source, plugin)
    (output / "plugin").symlink_to(plugin.relative_to(output), target_is_directory=True)
    for target, directory in (("pi", ".pi/plugins"), ("hermes", ".hermes/plugins")):
        if target in targets:
            destination = output / directory / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(
                os.path.relpath(plugin, destination.parent), target_is_directory=True
            )
    return plugin


def build_plugin(source: Path, output: Path, targets: tuple[str, ...]) -> None:
    source = source.resolve(strict=True)
    output = output.absolute()
    name = read_portable_plugin(source, targets)
    if output.resolve().is_relative_to(source):
        raise ValueError("Output must be outside the plugin source")
    output.mkdir()
    try:
        adapters = tuple(target for target in targets if target not in {"pi", "hermes"})
        if not adapters:
            deliver_package(source, output, name, targets)
            return
        prepare_workspace(source, output, name, adapters)
        with tempfile.TemporaryDirectory(prefix="agent-plugin-build-") as state:
            environment = os.environ | {
                "HOME": state,
                "XDG_CONFIG_HOME": state,
                "XDG_CACHE_HOME": state,
                "XDG_STATE_HOME": state,
                "NO_COLOR": "1",
            }
            environment.pop("BASH_ENV", None)
            run_dotagents("install", output, environment)
            run_dotagents("doctor", output, environment)
            plugin = deliver_package(source, output, name, targets)
            if (
                "claude" in targets
                and not (source / ".claude-plugin/plugin.json").exists()
            ):
                write_claude_mcp(
                    plugin,
                    environment["AGENT_PLUGIN_MCP_SHELL"],
                )
            if "opencode" in targets:
                write_opencode_mcp(output, name)
        remove_build_inputs(output)
    except BaseException:
        shutil.rmtree(output)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deliver a complete Agent Plugins v1 package with optional harness registration."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", action="append", default=[])
    arguments = parser.parse_args()
    try:
        build_plugin(arguments.source, arguments.output, tuple(arguments.target))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"agent-plugin-build: {error}\n")
    print(arguments.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
