from pathlib import PurePosixPath

import pytest

from instructions.instruction_projection import (
    project_instruction_documents,
    project_skill_directory,
)
from instructions.instruction_link_targets import instruction_link_violations
from instructions.ai_instruction_format import inspect_markdown_instruction


def test_assembles_metadata_and_rules_before_validating():
    documents = [
        {"source": "/source/metadata.md", "text": "---\nname: core\n---\n"},
        {"source": "/source/core.md", "text": "### Evidence\n\nRead.\n"},
    ]
    rendered = project_instruction_documents(
        documents, PurePosixPath("/home/core/SKILL.md"), {}
    )
    assert rendered == "---\nname: core\n---\n\n### Evidence\n\nRead.\n"


def test_rejects_duplicate_sections_in_an_actual_assembly():
    documents = [
        {"source": "/source/one.md", "text": "### Evidence\n\nRead.\n"},
        {"source": "/source/two.md", "text": "### Evidence\n\nVerify.\n"},
    ]
    with pytest.raises(ValueError, match="unique heading anchor"):
        project_instruction_documents(documents, PurePosixPath("/home/AGENTS.md"), {})


def test_generated_prose_wraps_without_turning_inline_steps_into_a_list():
    text = (
        "### Scope\n\n"
        + "Read carefully. " * 7
        + "1) read; 2) verify `literal  spacing`.\n"
    )
    rendered = project_instruction_documents(
        [{"source": "/source.md", "text": text}], PurePosixPath("/home/AGENTS.md"), {}
    )
    assert max(map(len, rendered.splitlines())) <= 120
    assert "`literal  spacing`" in rendered
    assert not inspect_markdown_instruction(rendered).violations


def test_projection_rejects_a_paragraph_that_grows_past_six_lines_when_wrapped():
    text = "### Scope\n\n" + "Read the source carefully. " * 32 + "\n"
    with pytest.raises(ValueError, match="at most 6 prose lines per paragraph"):
        project_instruction_documents(
            [{"source": "/source.md", "text": text}],
            PurePosixPath("/home/AGENTS.md"),
            {},
        )


def test_projection_preserves_authored_paragraph_boundaries_when_wrapping():
    paragraphs = [
        "Read the source carefully. " * 16,
        "Verify the source carefully. " * 16,
    ]
    text = "### Scope\n\n" + "\n\n".join(paragraphs)
    rendered = project_instruction_documents(
        [{"source": "/source.md", "text": text}], PurePosixPath("/home/AGENTS.md"), {}
    )
    assert [" ".join(block.split()) for block in rendered.split("\n\n")[1:]] == [
        paragraph.strip() for paragraph in paragraphs
    ]
    assert not inspect_markdown_instruction(rendered).violations


def test_projects_a_skill_and_preserves_its_template_and_executable(tmp_path):
    source = tmp_path / "source/read"
    source.mkdir(parents=True)
    (source / "references").mkdir()
    (source / "assets").mkdir()
    (source / "SKILL.md").write_text(
        "### Scope\n\nRead [reference](references/action.md).\n"
    )
    (source / "references/action.md").write_text(
        "### Action\n\nRead [core](../../core.md#evidence) and [template](../assets/report.md).\n"
    )
    template = "# Report\n\n- <example>\n"
    (source / "assets/report.md").write_text(template)
    executable = source / "execute"
    executable.write_text("exit 0\n")
    executable.chmod(0o755)
    deployed = tmp_path / "home/.codex/skills/read"
    core = tmp_path / "home/.codex/AGENTS.md"
    core.parent.mkdir(parents=True)
    core.write_text("### Evidence\n\nRead.\n")
    destinations = {
        PurePosixPath("/canonical/read"): PurePosixPath(deployed),
        PurePosixPath("/canonical/core.md"): PurePosixPath(core),
    }
    project_skill_directory(
        source,
        deployed,
        PurePosixPath("/canonical/read"),
        PurePosixPath(deployed),
        destinations,
    )
    reference = deployed / "references/action.md"
    assert (
        instruction_link_violations(
            reference, inspect_markdown_instruction(reference.read_text()), {}
        )
        == []
    )
    assert (deployed / "assets/report.md").read_text() == template
    assert (deployed / "execute").stat().st_mode & 0o111 == 0o111
    assert "../../core.md" in (source / "references/action.md").read_text()


def test_rejects_unsupported_markdown_in_a_copied_reference(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "SKILL.md").write_text("### Scope\n\nRead.\n")
    (source / "references").mkdir()
    (source / "references/action.md").write_text("### Action\n\n- Unsupported.\n")
    with pytest.raises(ValueError, match="heading followed by nonempty prose"):
        project_skill_directory(
            source,
            tmp_path / "output",
            PurePosixPath("/source"),
            PurePosixPath("/deployed"),
            {},
        )
