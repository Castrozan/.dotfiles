#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
HUMAN_FACING_REPLY_MODULES_DIRECTORY = (
    REPOSITORY_ROOT
    / "agent-harness"
    / "hooks"
    / "runtime"
    / "common"
    / "human_facing_reply"
)
ENFORCED_REPLY_RULES_SURFACE = (
    REPOSITORY_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "core-rules"
    / "communication"
    / "enforced-reply-rules.md"
)
EVERY_CHANNEL_WORDING_RULES_SURFACE = (
    REPOSITORY_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "enforced-wording-rules.md"
)

sys.path.insert(0, str(HUMAN_FACING_REPLY_MODULES_DIRECTORY))

from reply_rule_rendering import (  # noqa: E402
    rendered_enforced_reply_rules_markdown,
    rendered_every_channel_wording_rules_markdown,
)

GENERATED_SURFACES = (
    (ENFORCED_REPLY_RULES_SURFACE, rendered_enforced_reply_rules_markdown),
    (
        EVERY_CHANNEL_WORDING_RULES_SURFACE,
        rendered_every_channel_wording_rules_markdown,
    ),
)


def main() -> None:
    for surface_path, render in GENERATED_SURFACES:
        surface_path.write_text(render(), encoding="utf-8")
        print(f"wrote {surface_path.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
