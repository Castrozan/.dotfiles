#!/usr/bin/env python3

"""Name the Servant this session is, derived from the id the harness minted itself.

The launch wrapper cannot do this. It runs before the session exists, so it would
have to mint an id and hand it back through a flag, and only Claude Code accepts
one (--session-id). SessionStart fires after the harness has made its own id, and
fires again with that same id on a resume and on a compact, so deriving the
Servant here keeps one conversation on one Servant with nothing persisted, no
launch flag, and no per-harness launch code.

This handler supplies only the value. The rule that gives it force lives in the
appended system prompt (core-rules/servant-identity.md), because context injected
by a hook arrives as ambient material the session is told not to act on. Register
this handler only on surfaces whose interactive prompt carries that rule, or the
name arrives with nothing to bind it.
"""

from __future__ import annotations

import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"

servants_domain_directory = Path("@servantsDomainDirectory@")
if not servants_domain_directory.is_dir():
    # The placeholder is unsubstituted, so this is the repo tree rather than the
    # nix-built flat hooks directory, and the domain sits beside the hooks root.
    servants_domain_directory = hook_script_directory.parents[2] / "servants"

for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
    servants_domain_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

from catalog import select_servant_for_session  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402
from interactive_session_detection import (  # noqa: E402
    is_clawde_background_agent_session,
)

# Claude Code names it session_id; the other harnesses register the same hook
# config shape but have not all settled on the same key for the conversation.
SESSION_ID_PAYLOAD_KEYS = ("session_id", "conversation_id", "thread_id")


def session_id_of(hook_input: dict) -> str:
    for payload_key in SESSION_ID_PAYLOAD_KEYS:
        session_id = hook_input.get(payload_key, "")
        if session_id:
            return str(session_id)
    return ""


def servant_context_line(servant: dict) -> str:
    return f"Servant: {servant['name']} - {servant['personality']}"


def handle(hook_input: dict):
    """The Servant line for this session, or nothing when it has no identity to draw.

    A clawde agent already carries a name and a personality of its own, so it is
    left alone. A payload with no id would make every such session draw the same
    Servant, which is worse than staying silent and letting the rule find none.
    """
    if is_clawde_background_agent_session():
        return None
    session_id = session_id_of(hook_input)
    if not session_id:
        return None
    return HandlerResult(
        additional_context=servant_context_line(select_servant_for_session(session_id))
    )
