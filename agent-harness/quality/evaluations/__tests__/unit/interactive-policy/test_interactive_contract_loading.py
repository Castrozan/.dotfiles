from interactive_surface_support import (
    INTERACTIVE_GENERATOR_PATHS,
    INTERACTIVE_LAUNCH_SOURCES,
    INTERACTIVE_POLICY_SOURCE,
    ON_DEMAND_HUMANIZE_SOURCES,
    interactive_policy_section,
)


def test_each_harness_injects_only_the_interactive_contract():
    for launcher_path in INTERACTIVE_GENERATOR_PATHS:
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


def test_explicit_wellput_request_loads_before_other_actions():
    wellput_loading = interactive_policy_section("explicit_wellput_requests")

    assert "explicitly asked to use the `wellput` skill" in wellput_loading
    assert "before any other action" in wellput_loading
