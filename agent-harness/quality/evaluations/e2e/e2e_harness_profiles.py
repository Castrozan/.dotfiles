from dataclasses import dataclass

UNPROFILED_HARNESS_ADMISSION_CRITERIA = (
    "A harness earns an e2e profile only after a live probe records four facts: the "
    "manual compaction trigger, the confirmation marker printed when it compacts, the "
    "refusal marker printed when it declines, and whether pressing Enter on a typed "
    "slash directive submits that directive or selects the highlighted command-palette "
    "entry instead. opencode 1.18.18 fails the first fact: its palette exposes no "
    "compaction command, it compacts only when its own context threshold is reached, "
    "and a typed slash directive there submits the highlighted palette entry rather "
    "than the typed text."
)


@dataclass(frozen=True)
class HarnessProfile:
    name: str
    executable_name: str
    launch_arguments_template: str
    project_instruction_filename: str
    supports_instruction_reference_import: bool
    compaction_directive: str
    compaction_confirmation_marker: str
    compaction_refusal_marker: str

    def launch_command(self, model: str) -> str:
        arguments = self.launch_arguments_template.format(model=model)
        return f"{self.executable_name} {arguments}"


CLAUDE_PROFILE = HarnessProfile(
    name="claude",
    executable_name="claude",
    launch_arguments_template="--model {model} --dangerously-skip-permissions",
    project_instruction_filename="CLAUDE.md",
    supports_instruction_reference_import=True,
    compaction_directive="/compact",
    compaction_confirmation_marker="Compacted",
    compaction_refusal_marker="Not enough messages to compact",
)

CODEX_PROFILE = HarnessProfile(
    name="codex",
    executable_name="codex",
    launch_arguments_template="--sandbox danger-full-access --ask-for-approval never",
    project_instruction_filename="AGENTS.md",
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
