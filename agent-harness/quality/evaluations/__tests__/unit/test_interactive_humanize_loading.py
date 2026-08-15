from instruction_surface_scanner import REPO_ROOT


HUMANIZE_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "skills" / "humanize"
)
HUMANIZE_SKILL_PATH = HUMANIZE_DIRECTORY / "SKILL.md"
INTERACTIVE_POLICY_PATH = HUMANIZE_DIRECTORY / "interactive-communication.md"
COMMUNITY_LANGUAGE_PATH = HUMANIZE_DIRECTORY / "community-language.md"
MAXIMUM_ALWAYS_INJECTED_INTERACTIVE_POLICY_BYTES = 5000
MAXIMUM_ON_DEMAND_HUMANIZE_PACKAGE_BYTES = 19000

INTERACTIVE_POLICY_SOURCE = (
    "agent-instructions/skills/humanize/interactive-communication.md"
)
ON_DEMAND_HUMANIZE_SOURCES = (
    "agent-instructions/skills/humanize/SKILL.md",
    "agent-instructions/skills/humanize/community-language.md",
)
INTERACTIVE_LAUNCHER_PATHS = (
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "claude-code"
    / "skill-injection"
    / "interactive-sessions.nix",
    REPO_ROOT / "agent-harness" / "harnesses" / "codex" / "package.nix",
    REPO_ROOT / "agent-harness" / "harnesses" / "opencode" / "opencode.nix",
    REPO_ROOT / "agent-harness" / "harnesses" / "pi" / "package.nix",
)
INTERACTIVE_LAUNCH_SOURCES = (
    *INTERACTIVE_LAUNCHER_PATHS[:3],
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "pi"
    / "scripts"
    / "launch-pi-with-the-interactive-reply-rules.sh",
)


def test_each_harness_injects_only_the_interactive_contract():
    for launcher_path in INTERACTIVE_LAUNCHER_PATHS:
        launcher = launcher_path.read_text(encoding="utf-8")
        assert INTERACTIVE_POLICY_SOURCE in launcher
        for on_demand_source in ON_DEMAND_HUMANIZE_SOURCES:
            assert on_demand_source not in launcher
        assert "interactive-human-communication.md" not in launcher
        assert "interactive-hook-communication.md" not in launcher


def test_each_harness_marks_the_same_interactive_session_boundary():
    for launcher_path in INTERACTIVE_LAUNCH_SOURCES:
        assert "AGENT_INTERACTIVE_PREFERENCES_PATH" in launcher_path.read_text(
            encoding="utf-8"
        )


def test_interactive_contract_reconstructs_the_whole_session():
    policy = INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8")
    interactive_session = policy.split("<interactive-session>", 1)[1].split(
        "</interactive-session>", 1
    )[0]

    for required_context in (
        "multitasks",
        "may forget what the session is about",
        "whole session",
        "work-in-progress updates",
        "previous interaction",
        "earlier conversation",
    ):
        assert required_context in interactive_session

    for unrelated_session_type in (
        "background agents",
        "clawde",
        "headless runs",
        "subagents",
    ):
        assert unrelated_session_type not in interactive_session


def test_work_in_progress_updates_do_not_require_user_attention():
    policy = INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8")
    work_in_progress_updates = policy.split("<work-in-progress-updates>", 1)[1].split(
        "</work-in-progress-updates>", 1
    )[0]

    for required_behavior in (
        "Do not rely on the user reading work-in-progress updates",
        "best-supported decision",
        "within the task's scope",
        "require new authority",
        "final reply",
    ):
        assert required_behavior in work_in_progress_updates

    assert "report new evidence" not in work_in_progress_updates


def test_interactive_and_on_demand_surfaces_have_separate_context_budgets():
    always_injected_policy_bytes = len(INTERACTIVE_POLICY_PATH.read_bytes())
    assert (
        always_injected_policy_bytes <= MAXIMUM_ALWAYS_INJECTED_INTERACTIVE_POLICY_BYTES
    ), (
        "the always-injected interactive policy now exceeds its context budget at "
        f"{always_injected_policy_bytes} bytes"
    )

    on_demand_package_bytes = sum(
        len(path.read_bytes())
        for path in (HUMANIZE_SKILL_PATH, COMMUNITY_LANGUAGE_PATH)
    )
    assert on_demand_package_bytes <= MAXIMUM_ON_DEMAND_HUMANIZE_PACKAGE_BYTES, (
        "the on-demand Humanize package now exceeds its context budget at "
        f"{on_demand_package_bytes} bytes"
    )
