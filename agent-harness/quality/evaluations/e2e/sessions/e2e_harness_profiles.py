from dataclasses import dataclass
from pathlib import Path
from string import Template

UNPROFILED_HARNESS_ADMISSION_CRITERIA = (
    "A harness earns an e2e profile only after a live probe records six facts: the "
    "manual compaction trigger, the confirmation marker printed when it compacts, the "
    "refusal marker printed when it declines, the marker shown while a turn is still "
    "in flight, whether it blocks on a startup dialog in a fresh untrusted workspace "
    "and how to launch past it, and whether pressing Enter on typed text submits that "
    "text or selects a highlighted entry in a dialog or command palette. A harness "
    "that answers a modal with Enter silently swallows the first scenario prompt, and "
    "one whose busy indicator can hold still is graded as finished mid-turn. "
    "Verify the keystroke reached the application before recording any fact as "
    "missing: opencode was once rejected on a confirmation marker it does print, "
    "because the probe spelled the chord C-x, which herdr rejects with a non-zero "
    "exit, so the harness was judged on a compaction it never performed."
)


@dataclass(frozen=True)
class HarnessProfile:
    name: str
    executable_name: str
    launch_arguments_template: str
    project_instruction_filename: str
    busy_marker: str
    supports_instruction_reference_import: bool
    compaction_directive: str
    compaction_confirmation_marker: str
    compaction_refusal_marker: str
    compaction_prelude_keys: tuple[str, ...] = ()

    def launch_command(self, model: str, workspace_directory: Path) -> str:
        arguments = Template(self.launch_arguments_template).substitute(
            model=model, workspace_directory=workspace_directory
        )
        return f"{self.executable_name} {arguments}".strip()


CLAUDE_PROFILE = HarnessProfile(
    name="claude",
    executable_name="claude",
    launch_arguments_template="--model $model --dangerously-skip-permissions",
    project_instruction_filename="CLAUDE.md",
    busy_marker="",
    supports_instruction_reference_import=True,
    compaction_directive="/compact",
    compaction_confirmation_marker="Compacted",
    compaction_refusal_marker="Not enough messages to compact",
)

CODEX_PROFILE = HarnessProfile(
    name="codex",
    executable_name="codex",
    launch_arguments_template=(
        '-c \'projects={"$workspace_directory"={trust_level="trusted"}}\''
    ),
    project_instruction_filename="AGENTS.md",
    busy_marker="esc to interrupt",
    supports_instruction_reference_import=False,
    compaction_directive="/compact",
    compaction_confirmation_marker="Context compacted",
    compaction_refusal_marker="",
)

OPENCODE_PROFILE = HarnessProfile(
    name="opencode",
    executable_name="opencode",
    launch_arguments_template="--model $model",
    project_instruction_filename="AGENTS.md",
    busy_marker="esc interrupt",
    supports_instruction_reference_import=False,
    compaction_directive="compact",
    compaction_confirmation_marker="Compaction",
    compaction_refusal_marker="",
    compaction_prelude_keys=("ctrl+p",),
)

HARNESS_PROFILES = {
    profile.name: profile
    for profile in (CLAUDE_PROFILE, CODEX_PROFILE, OPENCODE_PROFILE)
}

DEFAULT_HARNESS_NAME = CLAUDE_PROFILE.name


def harness_profile(harness_name: str) -> HarnessProfile:
    profile = HARNESS_PROFILES.get(harness_name)
    if profile is None:
        raise ValueError(
            f"no e2e harness profile for '{harness_name}'. Available profiles are "
            f"{sorted(HARNESS_PROFILES)}. {UNPROFILED_HARNESS_ADMISSION_CRITERIA}"
        )
    return profile


def scenario_harness_profile(scenario: dict) -> HarnessProfile:
    return harness_profile(scenario.get("harness", DEFAULT_HARNESS_NAME))
