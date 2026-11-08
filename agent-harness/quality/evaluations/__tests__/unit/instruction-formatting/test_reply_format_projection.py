import copy
from pathlib import PurePosixPath

import pytest

from instructions.instruction_projection import (
    project_instruction_documents,
    project_skill_directory,
)
from instructions.instruction_surface_scanner import REPO_ROOT
from interactive_surface_support import pinned_wellput_reply_format_configuration


@pytest.fixture
def configured_reply_formats():
    configuration = copy.deepcopy(pinned_wellput_reply_format_configuration())
    configuration["formats"]["confirmation"]["maximum_words"] = 37
    configuration["lists"]["maximum_exempt_items"] = 2
    configuration["formats"]["labeled_reply"]["labels"][1]["grace_words"] = 7
    return configuration


def test_projection_expands_the_configuration_before_rebasing(configured_reply_formats):
    rendered = project_instruction_documents(
        [
            {
                "source": "/source/references/interactive.md",
                "text": "### Response shape\n\n{{reply_format}}\n",
            }
        ],
        PurePosixPath("/home/instructions.md"),
        {PurePosixPath("/source"): PurePosixPath("/home/skills/humanize")},
        configured_reply_formats,
    )

    assert "37 prose words or fewer" in rendered
    assert "up to 2 items" in rendered
    assert "done 20 + 7 words" in rendered
    assert "Every rendered table starts with a `#` index column" in rendered
    assert "skills/humanize/SKILL.md#representation-selection" in rendered
    assert "{{reply_format}}" not in rendered


def test_copied_skills_expand_the_same_configuration(
    tmp_path, configured_reply_formats
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "SKILL.md").write_text("### Scope\n\nRead.\n")
    (source / "references").mkdir()
    (source / "references/interactive.md").write_text(
        "### Response shape\n\n{{reply_format}}\n"
    )
    output = tmp_path / "output"

    project_skill_directory(
        source,
        output,
        PurePosixPath(source),
        PurePosixPath(output),
        {PurePosixPath(source): PurePosixPath(output)},
        configured_reply_formats,
    )

    assert (
        "37 prose words or fewer" in (output / "references/interactive.md").read_text()
    )


@pytest.mark.parametrize(
    "additional_sources",
    [
        [],
        [
            REPO_ROOT
            / "agent-harness/agent-instructions/core-rules/servant-identity.md",
            REPO_ROOT / "agent-harness/harnesses/codex/session-title-instructions.md",
        ],
    ],
)
def test_complete_interactive_instructions_fit_projection_limits(additional_sources):
    source = REPO_ROOT / "agent-harness/agent-instructions/interactive-communication.md"
    rendered = project_instruction_documents(
        [
            {"source": str(path), "text": path.read_text()}
            for path in [source, *additional_sources]
        ],
        PurePosixPath(
            "/nix/store/00000000000000000000000000000000-interactive-instructions.md"
        ),
        {
            PurePosixPath(source.parent / "core-rules/core.md"): PurePosixPath(
                "/home/agent/.claude/CLAUDE.md"
            ),
        },
        pinned_wellput_reply_format_configuration(),
    )

    assert "### Peer communication" in rendered
    assert "home/agent/.claude/CLAUDE.md#evidence)" in rendered
