import argparse
import json
import shutil
import subprocess
from pathlib import Path

from instructions.ai_instruction_format import inspect_markdown_instruction
from instructions.instruction_link_targets import instruction_link_violations
from instructions.instruction_markdown_frontmatter import parse_instruction_body
from instructions.instruction_surface_prose import line_is_exempt_from_the_wrap


def copy_projection(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(
            source, target, dirs_exist_ok=True, copy_function=shutil.copyfile
        )
    else:
        shutil.copyfile(source, target)


def verify_projections(manifest, filesystem_root: Path) -> None:
    filesystem_root = filesystem_root.resolve()
    home = filesystem_root / manifest["homeDirectory"].lstrip("/")
    bundle = Path(manifest["bundle"])
    shutil.copytree(
        bundle, filesystem_root / bundle.relative_to(bundle.anchor), symlinks=True
    )
    directories = [home]
    for name, source in manifest["homeFiles"].items():
        source = Path(source)
        target = home / name
        materialized_source = filesystem_root / source.relative_to(source.anchor)
        if source.is_dir() and materialized_source.is_dir():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(materialized_source, target_is_directory=True)
            directories.append(target)
        else:
            copy_projection(source, target)
    workflow = (
        home
        / ".local/share/agent-plugins/dotfiles/plugin/skills/research/research-pulse.workflow.js"
    )
    subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            "import {readFileSync} from 'node:fs'; "
            "const source = readFileSync(process.argv[1], 'utf8')"
            ".replace('export const meta =', 'const meta ='); "
            "const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor; "
            "new AsyncFunction('args', 'agent', 'phase', 'parallel', 'log', source);",
            str(workflow),
        ],
        check=True,
    )
    assert "const ITEMS_SCHEMA =" in workflow.read_text()
    assert "const researchSourcePrompts =" in workflow.read_text()
    instructions = list(
        {
            path
            for directory in directories
            for path in directory.rglob("*.md")
            if path.name in {"SKILL.md", "AGENTS.md", "CLAUDE.md", "SOUL.md"}
            or "references" in path.parts
            or path.is_relative_to(home / ".claude/agents")
            or path.is_relative_to(home / ".config/opencode/agent")
        }
    )
    for prompt in manifest["promptFiles"]:
        target = filesystem_root / prompt["destination"].lstrip("/")
        copy_projection(Path(prompt["source"]), target)
        instructions.append(target)
    assert len(instructions) > 100, "generated fixture omitted the deployed skill trees"
    inspections = {
        Path("/")
        / path.resolve().relative_to(filesystem_root): inspect_markdown_instruction(
            path.read_text()
        )
        for path in instructions
    }
    violations = []
    for path in instructions:
        logical = Path("/") / path.resolve().relative_to(filesystem_root)
        inspected = inspections[logical]
        for violation in inspected.violations + instruction_link_violations(
            logical, inspected, inspections, filesystem_root
        ):
            violations.append(f"{logical}: {violation.render()}")
        text = path.read_text()
        if len(text.splitlines()) > 200:
            violations.append(f"{logical}: expected at most 200 physical lines")
        body = parse_instruction_body(text)
        for number, line in enumerate(body.text.splitlines(), body.first_line_number):
            if len(line) > 120 and not line_is_exempt_from_the_wrap(line):
                violations.append(
                    f"{logical}:{number}: expected at most 120 prose columns"
                )
    assert not violations, "\n".join(violations)
    print(
        f"Verified {len(instructions)} generated instruction files and their deployed links."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("filesystem_root", type=Path)
    arguments = parser.parse_args()
    verify_projections(
        json.loads(arguments.manifest.read_text()), arguments.filesystem_root
    )


if __name__ == "__main__":
    main()
