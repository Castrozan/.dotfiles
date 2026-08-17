import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = HOOKS_ROOT.parents[2]
REPLY_RULE_MODULE_DIRECTORY = next(HOOKS_ROOT.rglob("reply_rule_catalog.py")).parent
if str(REPLY_RULE_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY))

from reply_rule_catalog import template_violations_in_reply  # noqa: E402
from reply_rule_feedback import bounce_guidance  # noqa: E402

INTERACTIVE_COMMUNICATION_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "interactive-communication.md"
)


def test_named_merge_request_without_a_direct_link_is_blocked():
    violations = template_violations_in_reply(
        "MR !41 is ready for review.", "is the change ready?"
    )

    assert violations == ["names an MR or PR but gives no link to validate it"]


def test_named_pull_request_with_a_direct_link_passes():
    reply = "PR #17 is ready: https://github.com/example/project/pull/17"

    assert template_violations_in_reply(reply, "is the change ready?") == []


def test_generic_merge_and_pull_request_terms_do_not_claim_an_artifact():
    reply = (
        "Pull request paths now trigger CI. The guide also explains how to open a "
        "merge request."
    )

    assert template_violations_in_reply(reply, "what changed in CI?") == []


def test_reply_shape_and_punctuation_are_not_hook_predicates():
    reply = """## Decision

Yes, the migration is safe to continue — the failed host was removed.

- The healthy hosts remain available.
- The replacement is reversible.

As I said earlier, the evidence is now included here so this reply stands alone.
"""

    assert template_violations_in_reply(reply, "review the migration") == []


def test_long_explanation_is_not_classified_by_a_regex_gate():
    reply = " ".join(["evidence"] * 600)

    assert template_violations_in_reply(reply, "explain the architecture") == []


def test_a_quoted_unlinked_artifact_inside_a_fence_does_not_block():
    reply = "The source says:\n```\nMR !41 is pending\n```\nNo artifact is named in my prose."

    assert template_violations_in_reply(reply, "quote the source") == []


def test_bounce_guidance_names_the_violation_and_routes_to_humanize():
    guidance = bounce_guidance(["names an MR or PR but gives no link to validate it"])

    assert "names an MR or PR" in guidance
    assert "load the humanize skill" in guidance.lower()
    assert "interactive communication instructions" in guidance


def test_interactive_instructions_route_substantive_output_to_humanize():
    policy = INTERACTIVE_COMMUNICATION_PATH.read_text(encoding="utf-8").lower()

    assert "load the humanize skill" in policy
    for reader_task in (
        "explanation",
        "diagnosis",
        "decision",
        "warning",
        "report",
        "summary",
    ):
        assert reader_task in policy


def test_interactive_contract_treats_explicit_short_requests_as_binding():
    policy = INTERACTIVE_COMMUNICATION_PATH.read_text(encoding="utf-8").lower()

    assert "tldr" in policy
    assert "binding" in policy
    assert "hard ceiling" not in policy
