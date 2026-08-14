from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_COMMON_MODULE_DIRECTORY = os.path.join(os.path.dirname(_MODULE_DIRECTORY), "common")
if _COMMON_MODULE_DIRECTORY not in sys.path:
    sys.path.insert(0, _COMMON_MODULE_DIRECTORY)

from hook_dispatch import HandlerResult  # noqa: E402
import skill_loaded_marker  # noqa: E402

HUMANIZE_SKILL_NAME = "humanize"
POST_COMPACTION_HUMANIZE_RELOAD_DIRECTIVE = (
    "Compaction removed the verified humanize skill context. Invoke "
    "Skill(skill='humanize') before the next human-facing reply; the Stop hook will "
    "block completion until the reload is recorded."
)


def handle(hook_input: dict):
    if hook_input.get("source", "") != "compact":
        return None
    skill_loaded_marker.clear_skill_loaded(
        HUMANIZE_SKILL_NAME, hook_input.get("session_id", "")
    )
    return HandlerResult(additional_context=POST_COMPACTION_HUMANIZE_RELOAD_DIRECTIVE)
