#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

from hook_dispatch import HandlerResult  # noqa: E402
from interactive_reply_reminder_state import (  # noqa: E402
    record_reply_reminder_injected,
    reply_reminder_should_be_injected,
)
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)

TLDR_REPLY_REMINDER = (
    "Reply as a short, well-written status report in plain prose, no lists and no numbering. "
    "Open with a header-less paragraph that answers directly and gives the cause or context so "
    "Lucas understands it fully, then a `**Done:**` line and a `**Next:**` line, each one or two "
    "plain sentences; a one or two sentence confirmation may be the opening paragraph alone. "
    "Aim for roughly 150 words in that shape, an opening paragraph plus a Done and Next of one or "
    "two lines each; a substantive turn may run to around 200, so keep the substance Lucas needs "
    "rather than amputate the answer, but never a multi-paragraph dump and never a Done or Next "
    "that swells into several paragraphs. "
    'No reaction or sycophancy openers, no mechanics narration ("Let me", "I\'ll go ahead"), no '
    "section headers, no repeated content, no em dashes, no pasted output. Include the link to "
    "any MR, PR, ticket, issue, or deploy the work produced so Lucas can validate it. Full "
    "context comes from well-chosen prose, not length. The Stop hook always bounces an em dash, a "
    "reaction or narration opener, and an MR or PR named without its link; it bounces lists, "
    "headers, a wall past roughly 250 prose words, and the missing Done or Next labels only when "
    "you were not explicitly asked for a document or an in-detail write-up."
)


def handle(hook_input: dict):
    if not is_keyboard_driven_interactive_session():
        return None
    session_id = hook_input.get("session_id") or ""
    if not reply_reminder_should_be_injected(session_id):
        return None
    record_reply_reminder_injected(session_id)
    return HandlerResult(additional_context=TLDR_REPLY_REMINDER)
