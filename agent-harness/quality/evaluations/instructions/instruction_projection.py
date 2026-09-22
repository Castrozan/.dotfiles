import argparse
import json
import shutil
import stat
from pathlib import Path, PurePosixPath

from instructions.ai_instruction_format import inspect_markdown_instruction
from instructions.instruction_link_rebasing import rebase_instruction_links
from instructions.instruction_prose_wrapping import wrap_instruction_prose
from instructions.reply_format_instructions import expand_reply_format_instructions


def project_instruction_documents(
    documents: list[dict[str, str]],
    deployed: PurePosixPath,
    destinations: dict[PurePosixPath, PurePosixPath],
    reply_format_configuration: dict | None = None,
) -> str:
    destinations = {
        **destinations,
        **{PurePosixPath(document["source"]): deployed for document in documents},
    }
    rendered = "\n".join(
        rebase_instruction_links(
            expand_reply_format_instructions(
                document["text"], reply_format_configuration
            ),
            PurePosixPath(document["source"]),
            deployed,
            destinations,
        )
        for document in documents
    )
    violations = inspect_markdown_instruction(rendered).violations
    if violations:
        raise ValueError("\n".join(violation.render() for violation in violations))
    rendered = wrap_instruction_prose(rendered)
    violations = inspect_markdown_instruction(rendered).violations
    if violations:
        raise ValueError("\n".join(violation.render() for violation in violations))
    return rendered


def project_skill_directory(
    source: Path,
    output: Path,
    canonical: PurePosixPath,
    deployed: PurePosixPath,
    destinations: dict[PurePosixPath, PurePosixPath],
    reply_format_configuration: dict | None = None,
) -> None:
    shutil.copytree(source, output)
    instruction_files = [
        output / "SKILL.md",
        *sorted((output / "references").rglob("*.md")),
    ]
    for instruction in instruction_files:
        relative = instruction.relative_to(output)
        rendered = project_instruction_documents(
            [{"source": str(canonical / relative), "text": instruction.read_text()}],
            deployed / relative,
            destinations,
            reply_format_configuration,
        )
        instruction.chmod(instruction.stat().st_mode | stat.S_IWUSR)
        instruction.write_text(rendered)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    manifest = json.loads(arguments.manifest.read_text())
    destinations = {
        PurePosixPath(source): PurePosixPath(target)
        for source, target in manifest["destinations"].items()
    }
    deployed = PurePosixPath(manifest["deployed"] or str(arguments.output))
    if "sourceDirectory" in manifest:
        project_skill_directory(
            Path(manifest["sourceDirectory"]),
            arguments.output,
            PurePosixPath(manifest["canonicalDirectory"]),
            deployed,
            destinations,
            manifest.get("replyFormatConfiguration"),
        )
        return
    arguments.output.write_text(
        project_instruction_documents(
            manifest["documents"],
            deployed,
            destinations,
            manifest.get("replyFormatConfiguration"),
        )
    )


if __name__ == "__main__":
    main()
