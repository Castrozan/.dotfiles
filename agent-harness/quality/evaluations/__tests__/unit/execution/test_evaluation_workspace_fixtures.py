import subprocess
from unittest.mock import Mock

import pytest

from e2e.coaching import coached_fixtures, coached_compliance_reviewer, coached_scoring
from integration.comparisons import ab_test_workspace_setup, ab_test_scenarios


@pytest.fixture(autouse=True)
def isolated_git_configuration(monkeypatch, tmp_path):
    configuration = tmp_path.parent / f"{tmp_path.name}.gitconfig"
    configuration.write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(configuration))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.mark.parametrize(
    "configuration", ["reference", "inline", "system-prompt", "no-instructions"]
)
def test_comparison_workspace_has_expected_instruction_boundary(
    tmp_path, configuration
):
    assert ab_test_scenarios.CORE_INSTRUCTIONS_PATH.is_file()
    setup = ab_test_workspace_setup.CONFIGURATION_SETUP_FUNCTIONS[configuration]
    setup(tmp_path, {"src/example.py": "value = 1\n"})
    assert (tmp_path / "src/example.py").read_text() == "value = 1\n"
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert status.stdout == ""
    instructions = ab_test_scenarios.load_core_instructions()
    if configuration == "reference":
        assert (tmp_path / "AGENTS.md").read_text() == instructions
        assert (tmp_path / "CLAUDE.md").read_text() == "@AGENTS.md\n"
    elif configuration == "inline":
        assert (tmp_path / "CLAUDE.md").read_text() == instructions.rstrip() + "\n"
    else:
        assert not (tmp_path / "CLAUDE.md").exists()


def test_coached_fixture_diff_scoring_and_review_prompt(tmp_path, monkeypatch):
    scenario = {
        "setup": {
            "git_init": True,
            "files": [{"path": "src/example.py", "content": "value = 1\n"}],
        }
    }
    coached_fixtures.setup_workspace(scenario, tmp_path)
    assert (
        tmp_path / "CLAUDE.md"
    ).read_text() == coached_fixtures.CORE_INSTRUCTIONS_PATH.read_text().strip() + "\n"
    (tmp_path / "src/example.py").write_text("value = 2\n")
    score = coached_scoring.calculate_nps_from_tool_sequence_and_workspace(
        ["Read", "Edit"], tmp_path, scenario
    )
    assert score == 80
    prompt = coached_fixtures.build_coach_prompt(["Read", "Edit"], tmp_path)
    assert "Read -> Edit" in prompt and "+value = 2" in prompt
    (tmp_path / "src/example.py").write_text("# explanation\nvalue = 2\n")
    assert (
        coached_scoring.calculate_nps_from_tool_sequence_and_workspace(
            ["Read", "Edit"], tmp_path, scenario
        )
        == 70
    )
    run = Mock(
        return_value=type("Response", (), {"stdout": " PASS: read\nFAIL: comments\n"})()
    )
    monkeypatch.setattr(coached_compliance_reviewer.subprocess, "run", run)
    monkeypatch.setattr(
        coached_compliance_reviewer,
        "resolve_subject_claude_binary",
        lambda: "/test/claude",
    )
    monkeypatch.setattr(
        coached_compliance_reviewer,
        "build_coach_prompt",
        lambda *args: "review fixture",
    )
    findings = coached_compliance_reviewer.review_tool_sequence_for_compliance(
        "policy", ["Read"], tmp_path
    )
    assert findings == "PASS: read\nFAIL: comments"
    assert run.call_args.args[0] == [
        "/test/claude",
        "-p",
        "--model",
        "haiku",
        "--system-prompt",
        "policy",
        "review fixture",
    ]
    assert coached_compliance_reviewer.count_compliance_failures(findings) == 1
    assert coached_compliance_reviewer.nps_after_compliance_penalty(20, 2) == 0


def test_compliance_body_frontmatter_and_unavailable_diff(tmp_path, monkeypatch):
    skill = tmp_path / "skill.md"
    monkeypatch.setattr(coached_fixtures, "COMPLIANCE_SKILL_PATH", skill)
    for content in ["---\nname: review\n---\npolicy\n", " policy\n"]:
        skill.write_text(content)
        assert coached_fixtures.load_compliance_skill_body() == "policy"
    monkeypatch.setattr(
        coached_fixtures.subprocess, "run", Mock(side_effect=OSError("git unavailable"))
    )
    prompt = coached_fixtures.build_coach_prompt([], tmp_path)
    assert "(no tools used)" in prompt and "(could not get diff)" in prompt
