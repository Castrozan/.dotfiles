import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


TARGET_RULE_FILES = {
    "claudecode": "CLAUDE.md",
    "codexcli": "AGENTS.md",
    "opencode": "AGENTS.md",
    "hermesagent": ".hermes.md",
}
TARGET_AGENT_DIRECTORIES = {
    "claudecode": ".claude/agents",
    "opencode": ".opencode/agents",
}
GENERATION_TIMEOUT_SECONDS = 30


def validate_output(source: Path, output: Path, core_instructions: Path) -> None:
    agent_files = {path.name for path in (source / "subagents").glob("*.md")}
    if not agent_files:
        raise ValueError("Canonical subagent definitions are missing")
    for target, rule_file in TARGET_RULE_FILES.items():
        directory = output / target
        expected = {rule_file}
        if target in TARGET_AGENT_DIRECTORIES:
            expected.update(
                f"{TARGET_AGENT_DIRECTORIES[target]}/{name}" for name in agent_files
            )
        actual = {
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
        }
        if actual != expected:
            raise ValueError(
                f"{target} output mismatch: missing={sorted(expected - actual)}, "
                f"unexpected={sorted(actual - expected)}"
            )
        if (directory / rule_file).read_bytes() != core_instructions.read_bytes():
            raise ValueError(f"{target} changed the shared core instructions")


def build_configuration(
    source: Path, output: Path, rulesync: Path, core_instructions: Path
) -> None:
    output.mkdir()
    try:
        with tempfile.TemporaryDirectory(prefix="rulesync-configuration-") as temporary:
            state = Path(temporary)
            for target in TARGET_RULE_FILES:
                home = state / target
                home.mkdir()
                environment = os.environ | {
                    "HOME": str(home),
                    "HERMES_HOME": str(home / "hermes"),
                    "XDG_CONFIG_HOME": str(home / ".config"),
                    "XDG_CACHE_HOME": str(home / ".cache"),
                    "XDG_STATE_HOME": str(home / ".local/state"),
                    "NO_COLOR": "1",
                }
                features = (
                    "rules,subagents" if target in TARGET_AGENT_DIRECTORIES else "rules"
                )
                subprocess.run(
                    [
                        str(rulesync),
                        "generate",
                        "--input-roots",
                        str(source),
                        "--output-roots",
                        str(output / target),
                        "--targets",
                        target,
                        "--features",
                        features,
                    ],
                    cwd=home,
                    env=environment,
                    check=True,
                    timeout=GENERATION_TIMEOUT_SECONDS,
                )
            validate_output(source, output, core_instructions)
    except BaseException:
        shutil.rmtree(output)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rulesync", required=True, type=Path)
    parser.add_argument("--core-instructions", required=True, type=Path)
    arguments = parser.parse_args()
    build_configuration(
        arguments.source.resolve(strict=True),
        arguments.output.resolve(),
        arguments.rulesync.resolve(strict=True),
        arguments.core_instructions.resolve(strict=True),
    )


if __name__ == "__main__":
    main()
