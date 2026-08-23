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


def test_opencode_takes_its_model_from_its_own_configuration():
    assert OPENCODE_PROFILE.launch_command("sonnet", "/tmp/workspace") == "opencode"
