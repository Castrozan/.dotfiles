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
    "opencode 1.18.18 fails the confirmation fact. It does compact on demand, through "
    "the ctrl+x c keybind rather than typed text, and that entry appears only once the "
    "session holds a message, which is why a fresh-session probe reported none. What "
    "it prints is a Compaction rule painted when compaction is requested; that title "
    "survived both a failed compaction and an interrupt, so it proves a request rather "
    "than a result. It also has no refusal marker, and on an empty session the second "
    "key leaks into the prompt composer."
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

HARNESS_PROFILES = {
    profile.name: profile for profile in (CLAUDE_PROFILE, CODEX_PROFILE)
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
