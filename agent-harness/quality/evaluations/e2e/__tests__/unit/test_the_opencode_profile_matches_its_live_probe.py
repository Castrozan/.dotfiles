from e2e_workspace import SCENARIOS_DIR, discover_scenario_files, load_scenario

from e2e_harness_profiles import (
    CLAUDE_PROFILE,
    CODEX_PROFILE,
    OPENCODE_PROFILE,
    harness_profile,
    scenario_harness_profile,
)


def test_opencode_is_admitted_by_name():
    assert harness_profile("opencode") is OPENCODE_PROFILE
    assert scenario_harness_profile({"harness": "opencode"}) is OPENCODE_PROFILE


def test_opencode_reaches_compaction_through_its_command_palette():
    assert OPENCODE_PROFILE.compaction_prelude_keys == ("ctrl+p",)
    assert OPENCODE_PROFILE.compaction_directive == "compact"


def test_only_opencode_needs_a_prelude_key():
    assert CLAUDE_PROFILE.compaction_prelude_keys == ()
    assert CODEX_PROFILE.compaction_prelude_keys == ()


def test_the_confirmation_marker_is_the_completion_line_not_the_palette_entry():
    assert OPENCODE_PROFILE.compaction_confirmation_marker == "Compaction"
    assert "Compact session" not in OPENCODE_PROFILE.compaction_confirmation_marker


def test_opencode_is_launched_with_the_model_it_is_given():
    assert (
        OPENCODE_PROFILE.launch_command("openai/gpt-5.4-mini", "/tmp/workspace")
        == "opencode --model openai/gpt-5.4-mini"
    )


def test_the_opencode_scenario_names_a_provider_qualified_model():
    scenario = load_scenario(
        SCENARIOS_DIR / "no-comments-survives-opencode-compaction.yaml"
    )
    assert "/" in scenario["model"]


def test_every_scenario_naming_a_model_runs_on_a_harness_that_needs_one():
    for scenario_file in discover_scenario_files(SCENARIOS_DIR):
        scenario = load_scenario(scenario_file)
        if "model" not in scenario:
            continue
        assert scenario_harness_profile(scenario) is OPENCODE_PROFILE
