from instruction_surface_scanner import REPO_ROOT

DOTFILES_REVIEW_PROCEDURE_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "review"
    / "dotfiles-change.md"
)
REVIEW_SKILL_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "review"
    / "SKILL.md"
)
PROJECT_CONTEXT_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "project-context"
    / "dotfiles-agent-instructions.md"
)
CLAUDE_WORKFLOW_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "claude-code"
    / "workflows"
    / "dotfiles-change-review.js"
)
PACKAGED_COMMANDS_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "workflow-commands"
    / "dotfiles-workflow-commands-home-manager.nix"
)


def procedure_source() -> str:
    return DOTFILES_REVIEW_PROCEDURE_PATH.read_text()


def test_project_context_routes_the_substantive_review_through_the_review_skill():
    scope = (
        PROJECT_CONTEXT_PATH.read_text()
        .split("<change-review-scope>", 1)[1]
        .split("</change-review-scope>", 1)[0]
    )
    assert "review" in scope and "dotfiles-change" in scope, (
        "the substantive pre-push review must be mandated as loading the review skill "
        "and following its dotfiles-change procedure, not a packaged command"
    )
    assert "cannot load skills" in scope, (
        "a harness without skill loading needs the repository fallback to the "
        "review skill files"
    )
    assert "skills/review/SKILL.md" in scope, (
        "the fallback must name the repository path of the review skill so the "
        "chapter is reachable without skill loading"
    )
    assert "`dotfiles-change-review`" not in scope, (
        "the project context must not name the retired packaged command"
    )


def test_the_review_skill_routes_the_dotfiles_procedure():
    skill = REVIEW_SKILL_PATH.read_text()
    specialized_audits = skill.split("<specialized-audits>", 1)[1]
    assert "dotfiles-change.md" in specialized_audits, (
        "the pre-push dotfiles change-review procedure must be reachable from "
        "the review skill's specialized-audits routing"
    )


def test_the_review_runs_inside_the_current_harness_without_extra_reviewers():
    source = procedure_source()
    mandate = source.split("<mandate>", 1)[1].split("</mandate>", 1)[0]
    assert "current harness" in mandate, (
        "the substantive review must be stated to run inside the current harness"
    )
    assert "no workflow" in mandate and "no reviewer subagent" in mandate, (
        "the procedure must launch neither a workflow nor a reviewer subagent"
    )
    assert "read-only until its verdict" in mandate, (
        "the procedure must be read-only until its verdict is delivered"
    )


def test_the_procedure_scopes_its_review_to_the_exact_task_commits():
    source = procedure_source()
    procedure = source.split("<procedure>", 1)[1]
    assert "exact task commit range" in procedure, (
        "the procedure must identify the exact commit range the task added"
    )
    assert "whole-range diff" in procedure, (
        "the procedure must read one whole-range diff rather than per-file diffs"
    )
    assert "excluding shared working-tree state and unrelated commits" in procedure, (
        "the procedure must exclude peers' uncommitted work and unrelated commits"
    )


def test_the_procedure_applies_all_six_review_lenses():
    procedure = procedure_source().replace(" ", "").lower()
    for lens in [
        "logic",
        "nix",
        "style",
        "instructions",
        "coverage",
        "exposure",
    ]:
        assert lens in procedure, (
            f"the procedure must review changed lines through the {lens} lens"
        )


def test_the_procedure_reports_clean_trees_with_a_goal_verdict():
    procedure = procedure_source()
    assert "No findings." in procedure, (
        "a clean review must report the parent contract's No findings. marker"
    )
    assert "verdict" in procedure, (
        "the procedure must close with a verdict on whether the goal is achieved"
    )


def test_findings_are_fixed_in_cohesive_follow_up_commits():
    follow_up = procedure_source().split("<follow-up>", 1)[1].lower()
    assert "cohesive follow-up commits" in follow_up, (
        "confirmed findings must be fixed in cohesive follow-up commits"
    )
    assert "never amend" in follow_up, (
        "the reviewed commit must not be amended because peers may have built on it"
    )


def test_the_claude_workflow_and_packaged_command_are_gone():
    assert not CLAUDE_WORKFLOW_PATH.exists(), (
        "the Claude-only change-review workflow must be deleted now that the "
        "procedure is owned by the cross-harness review skill"
    )
    assert "dotfiles-change-review" not in PACKAGED_COMMANDS_PATH.read_text(), (
        "the retired command must be removed from the packaged command list"
    )


def test_the_project_context_keeps_the_semantic_risk_classification():
    scope = (
        PROJECT_CONTEXT_PATH.read_text()
        .split("<change-review-scope>", 1)[1]
        .split("</change-review-scope>", 1)[0]
    )
    assert "substantive" in scope
    assert "non-semantic" in scope, (
        "the non-semantic exemption must survive the rewrite"
    )
    assert "rebuild" in scope, (
        "skipping the review must never excuse the rebuild or the tests"
    )
