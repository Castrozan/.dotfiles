import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = HOOKS_ROOT.parents[2]
REPLY_RULE_MODULE_DIRECTORY = next(HOOKS_ROOT.rglob("reply_rule_catalog.py")).parent
if str(REPLY_RULE_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY))

from reply_rule_catalog import template_violations_in_reply  # noqa: E402,F401
from reply_rule_feedback import bounce_guidance  # noqa: E402,F401

INTERACTIVE_COMMUNICATION_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "interactive-communication.md"
)

LABELED_REPLY = (
    "**brief:** the release gate.\n\n"
    "**done:** measured the candidate.\n\n"
    "**next:** push."
)


def labeled_reply_of(prose_words: int) -> str:
    body = " ".join(["evidence"] * prose_words)
    return f"**brief:** the release gate.\n\n**done:** {body}\n\n**next:** push."
