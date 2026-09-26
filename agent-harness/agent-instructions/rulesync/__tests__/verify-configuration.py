import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


EXPECTED_AGENT_NAMES = {"explore", "quality-assurance", "software-engineer"}


def read_agent(path: Path) -> tuple[dict, str]:
    content = path.read_text()
    opening, frontmatter, body = content.split("---", 2)
    assert not opening.strip(), f"Missing frontmatter opening: {path}"
    metadata = yaml.safe_load(frontmatter)
    assert isinstance(metadata, dict), f"Invalid agent metadata: {path}"
    return metadata, body.strip()


def verify_generated_configuration(
    configuration: Path, source: Path, core_instructions: Path
) -> None:
    expected_core = core_instructions.read_bytes()
    for relative_path in (
        "claudecode/CLAUDE.md",
        "codexcli/AGENTS.md",
        "opencode/AGENTS.md",
        "hermesagent/.hermes.md",
    ):
        assert (configuration / relative_path).read_bytes() == expected_core, (
            f"Shared instructions changed: {relative_path}"
        )
    for target, directory in (
        ("claudecode", ".claude/agents"),
        ("opencode", ".opencode/agents"),
    ):
        generated_directory = configuration / target / directory
        generated_names = {path.stem for path in generated_directory.glob("*.md")}
        assert generated_names == EXPECTED_AGENT_NAMES, (
            f"Unexpected native agents for {target}: {generated_names}"
        )
        for name in sorted(EXPECTED_AGENT_NAMES):
            canonical_metadata, canonical_body = read_agent(
                source / "subagents" / f"{name}.md"
            )
            generated_metadata, generated_body = read_agent(
                generated_directory / f"{name}.md"
            )
            expected_metadata = canonical_metadata[target] | {
                "name": canonical_metadata["name"],
                "description": canonical_metadata["description"],
            }
            assert generated_metadata == expected_metadata, (
                f"Native metadata changed: {target}/{name}"
            )
            assert generated_body == canonical_body, (
                f"Native instructions changed: {target}/{name}"
            )


def verify_malformed_agent_rejection(
    source: Path, rulesync: Path, builder: Path, core_instructions: Path
) -> None:
    with tempfile.TemporaryDirectory(prefix="rulesync-contract-") as temporary:
        directory = Path(temporary)
        malformed_source = directory / "source"
        shutil.copytree(source, malformed_source)
        malformed_agent = malformed_source / "subagents" / "explore.md"
        malformed_agent.chmod(0o644)
        malformed_agent.write_text(
            "---\ndescription: Invalid agent without name\n---\nInvalid agent body.\n"
        )
        ambient = directory / "ambient"
        ambient.mkdir()
        marker = ambient / "unrelated-state"
        marker.write_bytes(b"Preserve unrelated ambient state.\n")
        expected_marker = marker.read_bytes()
        environment = os.environ | {
            "HOME": str(ambient),
            "HERMES_HOME": str(ambient / "hermes"),
            "XDG_CONFIG_HOME": str(ambient / ".config"),
            "XDG_CACHE_HOME": str(ambient / ".cache"),
            "XDG_STATE_HOME": str(ambient / ".local/state"),
            "NO_COLOR": "1",
        }
        raw_output = directory / "raw-output"
        raw_result = subprocess.run(
            [
                str(rulesync),
                "generate",
                "--input-roots",
                str(malformed_source),
                "--output-roots",
                str(raw_output),
                "--targets",
                "claudecode",
                "--features",
                "rules,subagents",
            ],
            cwd=ambient,
            env=environment,
            capture_output=True,
            text=True,
            timeout=40,
        )
        assert raw_result.returncode == 0, raw_result.stderr
        assert "Failed to load subagent file" in raw_result.stderr
        raw_agents = raw_output / ".claude/agents"
        assert {path.stem for path in raw_agents.glob("*.md")} == (
            EXPECTED_AGENT_NAMES - {"explore"}
        ), "Rulesync did not reproduce the malformed-agent omission"
        rejected_output = directory / "rejected-configuration"
        adapter_result = subprocess.run(
            [
                sys.executable,
                str(builder),
                str(malformed_source),
                str(rejected_output),
                "--rulesync",
                str(rulesync),
                "--core-instructions",
                str(core_instructions),
            ],
            cwd=ambient,
            env=environment,
            capture_output=True,
            text=True,
            timeout=150,
        )
        assert adapter_result.returncode != 0, (
            "Build adapter accepted the malformed-agent omission"
        )
        assert "output mismatch" in adapter_result.stderr, adapter_result.stderr
        assert not rejected_output.exists(), "Rejected partial output remains"
        assert marker.read_bytes() == expected_marker, "Ambient state changed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--rulesync", required=True, type=Path)
    parser.add_argument("--builder", required=True, type=Path)
    parser.add_argument("--core-instructions", required=True, type=Path)
    arguments = parser.parse_args()
    verify_generated_configuration(
        arguments.configuration, arguments.source, arguments.core_instructions
    )
    verify_malformed_agent_rejection(
        arguments.source,
        arguments.rulesync,
        arguments.builder,
        arguments.core_instructions,
    )
    print(
        "Verified four core rule outputs, three Claude agents, three OpenCode agents, "
        "malformed-agent rejection, partial-output cleanup and ambient-state preservation"
    )


if __name__ == "__main__":
    main()
