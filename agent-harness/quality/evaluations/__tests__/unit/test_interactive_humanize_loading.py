from interactive_humanize_surface_support import (
    HUMANIZE_SKILL_PATH,
    INTERACTIVE_LAUNCHER_PATHS,
    INTERACTIVE_LAUNCH_SOURCES,
    INTERACTIVE_POLICY_PATH,
    INTERACTIVE_POLICY_SOURCE,
    MAXIMUM_ALWAYS_INJECTED_INTERACTIVE_POLICY_BYTES,
    MAXIMUM_ON_DEMAND_HUMANIZE_PACKAGE_BYTES,
    ON_DEMAND_HUMANIZE_SOURCES,
    interactive_policy_section,
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


def test_explicit_humanize_request_loads_before_other_actions():
    humanize_loading = interactive_policy_section("humanize_policy_loading")

    assert "explicitly requests Humanize" in humanize_loading
    assert "before any other action" in humanize_loading


def test_interactive_and_on_demand_surfaces_have_separate_context_budgets():
    always_injected_policy_bytes = len(INTERACTIVE_POLICY_PATH.read_bytes())
    assert (
        always_injected_policy_bytes <= MAXIMUM_ALWAYS_INJECTED_INTERACTIVE_POLICY_BYTES
    ), (
        "the always-injected interactive policy now exceeds its context budget at "
        f"{always_injected_policy_bytes} bytes"
    )

    on_demand_package_bytes = sum(
        len(path.read_bytes()) for path in (HUMANIZE_SKILL_PATH,)
    )
    assert on_demand_package_bytes <= MAXIMUM_ON_DEMAND_HUMANIZE_PACKAGE_BYTES, (
        "the on-demand Humanize package now exceeds its context budget at "
        f"{on_demand_package_bytes} bytes"
    )
