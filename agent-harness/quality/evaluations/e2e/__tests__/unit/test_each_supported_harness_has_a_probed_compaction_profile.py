import pytest
from e2e_harness_profiles import (
    CLAUDE_PROFILE,
    CODEX_PROFILE,
    HARNESS_PROFILES,
    harness_profile,
    scenario_harness_profile,
)


def test_a_scenario_without_a_harness_key_runs_on_claude():
    assert scenario_harness_profile({}) is CLAUDE_PROFILE
    assert scenario_harness_profile({"harness": "codex"}) is CODEX_PROFILE


def test_an_unprofiled_harness_names_the_probe_that_would_admit_it():
    with pytest.raises(ValueError) as rejection:
        harness_profile("opencode")
    rejection_text = str(rejection.value)
    assert "command-palette" in rejection_text
    assert "compaction" in rejection_text
    assert "opencode 1.18.18" in rejection_text


def test_every_profile_carries_a_directive_and_a_confirmation_marker():
    for profile in HARNESS_PROFILES.values():
        assert profile.compaction_directive
        assert profile.compaction_confirmation_marker


def test_claude_launches_on_the_requested_model_and_codex_on_its_configured_one():
    assert CLAUDE_PROFILE.launch_command("sonnet") == (
        "claude --model sonnet --dangerously-skip-permissions"
    )
    assert "--model" not in CODEX_PROFILE.launch_command("sonnet")
    assert CODEX_PROFILE.launch_command("sonnet").startswith("codex ")


def test_each_harness_reads_its_own_project_instruction_filename():
    assert CLAUDE_PROFILE.project_instruction_filename == "CLAUDE.md"
    assert CODEX_PROFILE.project_instruction_filename == "AGENTS.md"
    assert CLAUDE_PROFILE.supports_instruction_reference_import
    assert not CODEX_PROFILE.supports_instruction_reference_import
