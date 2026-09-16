from pathlib import Path, PurePosixPath

import pytest

from instructions.instruction_link_targets import instruction_link_violations
from instructions.instruction_link_rebasing import rebase_instruction_links
from instructions.ai_instruction_format import inspect_markdown_instruction


def write_instruction(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def violations_for(path):
    return instruction_link_violations(
        path, inspect_markdown_instruction(path.read_text()), {}
    )


def test_resolves_same_file_cross_file_unicode_and_template_links(tmp_path):
    source = write_instruction(
        tmp_path,
        "skills/read/SKILL.md",
        "### Evidence\n\nRead [here](#evidence), "
        "[preparation](../act/SKILL.md#prepara%C3%A7%C3%A3o), "
        "[the template](references/report.md), and [docs](https://example.com/doc#section).\n",
    )
    write_instruction(tmp_path, "skills/act/SKILL.md", "### Preparação\n\nPrepare.\n")
    write_instruction(
        tmp_path,
        "skills/read/references/report.md",
        "h2. Report\n\n* *Reason:* <reason>\n",
    )
    assert violations_for(source) == []


@pytest.mark.parametrize(
    ("target", "expected_rule"),
    [
        ("#missing", "instruction_link_anchor"),
        ("missing.md", "instruction_link_file"),
        ("references", "instruction_link_file"),
        ("references/report.md#missing", "instruction_link_anchor"),
        ("#%C3", "instruction_link_destination"),
    ],
)
def test_rejects_missing_files_anchors_and_invalid_encoded_destinations(
    tmp_path, target, expected_rule
):
    source = write_instruction(
        tmp_path, "SKILL.md", f"### Evidence\n\nRead [the destination]({target}).\n"
    )
    write_instruction(tmp_path, "references/report.md", "# Report\n\nTemplate.\n")
    violations = violations_for(source)
    assert [(violation.rule, violation.line_number) for violation in violations] == [
        (expected_rule, 3)
    ]


def test_accepts_an_existing_heading_in_a_non_instruction_document(tmp_path):
    source = write_instruction(
        tmp_path, "SKILL.md", "### Evidence\n\nRead [the template](report.md#report).\n"
    )
    write_instruction(tmp_path, "report.md", "# Report\n\n- Template content.\n")
    assert violations_for(source) == []


def test_checks_deployed_locations_without_following_source_symlink_parents(tmp_path):
    source = write_instruction(
        tmp_path,
        "source/skills/read/SKILL.md",
        "### Evidence\n\nRead [core](../../core-rules/core.md#evidence).\n",
    )
    write_instruction(tmp_path, "source/core-rules/core.md", "### Evidence\n\nRead.\n")
    deployed_directory = tmp_path / "home/.codex/skills/read"
    deployed_directory.parent.mkdir(parents=True)
    deployed_directory.symlink_to(source.parent, target_is_directory=True)
    assert violations_for(source) == []
    assert [
        violation.rule for violation in violations_for(deployed_directory / "SKILL.md")
    ] == ["instruction_link_file"]


def test_reads_a_repeated_anchor_target_once_per_validation_pass(tmp_path, monkeypatch):
    source = write_instruction(
        tmp_path,
        "SKILL.md",
        "### Evidence\n\nRead [one](target.md#one) and [two](target.md#two).\n",
    )
    target = write_instruction(
        tmp_path, "target.md", "# One\n\nRead.\n\n# Two\n\nAct.\n"
    )
    inspection = inspect_markdown_instruction(source.read_text())
    read_text = Path.read_text
    reads = []

    def count_reads(path, *arguments, **keywords):
        reads.append(path)
        return read_text(path, *arguments, **keywords)

    monkeypatch.setattr(Path, "read_text", count_reads)
    assert instruction_link_violations(source, inspection, {}) == []
    assert reads == [target]


def test_rebased_instruction_links_resolve_in_the_installed_layout(tmp_path):
    original = "### Evidence\n\nRead [core](../../core-rules/core.md#evidence).\n"
    source = write_instruction(tmp_path, "source/skills/read/SKILL.md", original)
    core = write_instruction(
        tmp_path, "source/core-rules/core.md", "### Evidence\n\nRead.\n"
    )
    deployed = tmp_path / "home/.codex/skills/read/SKILL.md"
    deployed_core = write_instruction(
        tmp_path, "home/.codex/skills/core/SKILL.md", core.read_text()
    )
    projected = rebase_instruction_links(
        original,
        PurePosixPath(source),
        PurePosixPath(deployed),
        {
            PurePosixPath(source.parent): PurePosixPath(deployed.parent),
            PurePosixPath(core): PurePosixPath(deployed_core),
        },
    )
    write_instruction(tmp_path, str(deployed.relative_to(tmp_path)), projected)
    assert violations_for(deployed) == []
    assert source.read_text() == original


def test_checks_absolute_installed_destinations_inside_a_staged_filesystem(tmp_path):
    source = Path("/home/example/SKILL.md")
    target = write_instruction(
        tmp_path, "home/example/core.md", "### Evidence\n\nRead.\n"
    )
    inspection = inspect_markdown_instruction(
        "### Scope\n\nRead [core](/home/example/core.md#evidence).\n"
    )
    assert instruction_link_violations(source, inspection, {}, tmp_path) == []
    target.unlink()
    assert [
        violation.rule
        for violation in instruction_link_violations(source, inspection, {}, tmp_path)
    ] == ["instruction_link_file"]
