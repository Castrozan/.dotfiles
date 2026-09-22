import json
from pathlib import PurePosixPath
from types import SimpleNamespace

import pytest

from instructions.instruction_projection import (
    project_instruction_documents,
    project_skill_directory,
)
from instructions.instruction_surface_scanner import REPO_ROOT
from instructions.reply_format_instructions import REPLY_FORMAT_CONFIGURATION_PATH
from runner import run_evals_config_loader
from runner.baseline.run_evals_fingerprint import digest_instruction_paths


@pytest.fixture
def configured_reply_formats():
    configuration = json.loads(
        (REPO_ROOT / REPLY_FORMAT_CONFIGURATION_PATH).read_text()
    )
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


def test_evaluation_loader_uses_the_worktree_configuration(
    tmp_path, monkeypatch, configured_reply_formats
):
    configuration_path = tmp_path / REPLY_FORMAT_CONFIGURATION_PATH
    configuration_path.parent.mkdir(parents=True)
    configuration_path.write_text(json.dumps(configured_reply_formats))
    instruction = tmp_path / "interactive.md"
    instruction.write_text("### Response shape\n\n{{reply_format}}\n")
    monkeypatch.setattr(run_evals_config_loader, "REPO_ROOT", tmp_path)

    prompt = run_evals_config_loader.resolve_system_prompt_for_test(
        {"skill_path": "interactive.md"}
    )

    assert "37 prose words or fewer" in prompt
    assert "{{reply_format}}" not in prompt


def test_historical_prompts_read_configuration_from_the_same_revision(
    monkeypatch, configured_reply_formats
):
    calls = []

    def git_show(command, **arguments):
        calls.append(command)
        content = (
            json.dumps(configured_reply_formats)
            if command[-1].endswith(".json")
            else "{{reply_format}}"
        )
        return SimpleNamespace(returncode=0, stdout=content)

    monkeypatch.setattr(run_evals_config_loader.subprocess, "run", git_show)

    prompt = run_evals_config_loader.load_skill_body_from_git_ref(
        "interactive.md", "previous"
    )

    assert "37 prose words or fewer" in prompt
    assert calls[-1] == ["git", "show", f"previous:{REPLY_FORMAT_CONFIGURATION_PATH}"]


def test_configuration_changes_invalidate_instruction_evidence(
    tmp_path, configured_reply_formats
):
    configuration_path = tmp_path / REPLY_FORMAT_CONFIGURATION_PATH
    configuration_path.parent.mkdir(parents=True)
    configuration_path.write_text(json.dumps(configured_reply_formats))
    instruction = tmp_path / "interactive.md"
    instruction.write_text("{{reply_format}}")
    previous = digest_instruction_paths(tmp_path, {instruction})

    configured_reply_formats["formats"]["confirmation"]["maximum_words"] += 1
    configuration_path.write_text(json.dumps(configured_reply_formats))

    assert digest_instruction_paths(tmp_path, {instruction}) != previous
