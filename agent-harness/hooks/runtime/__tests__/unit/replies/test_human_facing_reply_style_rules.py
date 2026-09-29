import json

from end_of_turn_format_guard_test_support import invoke_guard
from human_facing_reply_test_support import (
    INTERACTIVE_COMMUNICATION_PATH,
    LABELED_REPLY,
    bounce_guidance,
    template_violations_in_reply,
)


def test_generic_merge_and_pull_request_terms_do_not_claim_an_artifact():
    reply = (
        "Pull request paths now trigger CI. The guide also explains how to open a "
        "merge request."
    )

    assert template_violations_in_reply(reply) == []


def test_section_headers_remain_available():
    reply = f"## Decision\n\n{LABELED_REPLY}"

    assert template_violations_in_reply(reply) == []


def test_the_request_text_no_longer_gates_any_rule():
    reply = " ".join(["evidence"] * 111)

    for request in ("explain the architecture", "quick question", "write a full audit"):
        result = invoke_guard(
            {
                "hook_event_name": "Stop",
                "reply_text": reply,
                "user_request_text": request,
            }
        )
        assert (
            "runs 111 prose words, past the 100-word confirmation, but omits the "
            "What is this session about?:/done:/next: label"
        ) in json.loads(result.stdout)["reason"]


def test_bounce_guidance_names_the_violation_and_demands_a_repair_in_place():
    guidance = bounce_guidance(["names an MR or PR but gives no link to validate it"])

    assert "names an MR or PR" in guidance
    assert "interactive communication instructions" in guidance
    assert "load the humanize skill" not in guidance.lower()


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
