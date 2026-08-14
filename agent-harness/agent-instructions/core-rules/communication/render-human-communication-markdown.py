#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
HUMAN_FACING_REPLY_MODULES_DIRECTORY = (
    REPOSITORY_ROOT
    / "agent-harness"
    / "hooks"
    / "runtime"
    / "common"
    / "human_facing_reply"
)
INTERACTIVE_HUMAN_COMMUNICATION_SURFACE = (
    REPOSITORY_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "core-rules"
    / "communication"
    / "interactive-human-communication.md"
)
INTERACTIVE_HOOK_COMMUNICATION_SURFACE = (
    REPOSITORY_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "core-rules"
    / "communication"
    / "interactive-hook-communication.md"
)
HUMANIZE_DIRECTORY = (
    REPOSITORY_ROOT / "agent-harness" / "agent-instructions" / "skills" / "humanize"
)

sys.path.insert(0, str(HUMAN_FACING_REPLY_MODULES_DIRECTORY))

from reply_rule_rendering import (  # noqa: E402
    rendered_every_channel_wording_rules_markdown,
    rendered_interactive_human_communication_markdown as render_full_surface,
    rendered_interactive_hook_communication_markdown,
)

HUMAN_READABLE_OUTPUT_OPENING_TAG = "<human-readable-output>"
HUMAN_READABLE_OUTPUT_CLOSING_TAG = "</human-readable-output>"


def human_readable_output_policy_markdown() -> str:
    skill_text = (HUMANIZE_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
    opening_index = skill_text.index(HUMAN_READABLE_OUTPUT_OPENING_TAG)
    closing_index = skill_text.index(HUMAN_READABLE_OUTPUT_CLOSING_TAG) + len(
        HUMAN_READABLE_OUTPUT_CLOSING_TAG
    )
    return skill_text[opening_index:closing_index] + "\n"


def rendered_interactive_human_communication_markdown() -> str:
    return render_full_surface(human_readable_output_policy_markdown())


GENERATED_SURFACES = (
    (
        INTERACTIVE_HUMAN_COMMUNICATION_SURFACE,
        rendered_interactive_human_communication_markdown,
    ),
    (
        INTERACTIVE_HOOK_COMMUNICATION_SURFACE,
        rendered_interactive_hook_communication_markdown,
    ),
    (
        HUMANIZE_DIRECTORY / "enforced-wording-rules.md",
        rendered_every_channel_wording_rules_markdown,
    ),
)


def main() -> None:
    for surface_path, render in GENERATED_SURFACES:
        surface_path.write_text(render(), encoding="utf-8")
        print(f"wrote {surface_path.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
