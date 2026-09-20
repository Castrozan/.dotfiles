import json

from end_of_turn_format_guard_test_support import (
    assistant_text_event,
    invoke_guard,
    stop_payload,
    user_event,
    write_transcript_from_events,
    write_transcript_with_request_and_reply,
)


def test_blocks_merge_request_without_a_direct_link(tmp_path):
    transcript = write_transcript_with_request_and_reply(
        tmp_path,
        "is the change ready?",
        "MR !15 is ready for review.",
    )
    result = invoke_guard(stop_payload(transcript))
    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert "link" in parsed["reason"]


def test_blocks_pull_request_without_a_direct_link(tmp_path):
    transcript = write_transcript_with_request_and_reply(
        tmp_path,
        "is the change ready?",
        "The pull request is ready for review.",
    )
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_judges_only_the_final_reply_for_unlinked_artifacts(tmp_path):
    transcript = write_transcript_from_events(
        tmp_path,
        [
            user_event("first question"),
            assistant_text_event("MR !14 is ready without a link."),
            user_event("second question"),
            assistant_text_event("PR #17: https://github.com/acme/repo/pull/17"),
        ],
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_a_mechanical_only_violation_returns_the_corrected_reply(tmp_path):
    transcript = write_transcript_with_request_and_reply(
        tmp_path,
        "review the migration",
        "**what is this session about?:** the gate.\n\n"
        "**done:** the host was removed — the migration is safe.\n\n"
        "**next:** push.",
    )
    result = invoke_guard(stop_payload(transcript))
    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert "verbatim" in parsed["reason"]
    assert "the host was removed, the migration is safe." in parsed["reason"]


def test_a_reply_past_the_word_ceiling_still_demands_a_rewrite(tmp_path):
    transcript = write_transcript_with_request_and_reply(
        tmp_path,
        "review the migration",
        "**what is this session about?:** the gate — measured.\n\n"
        "**done:** " + "evidence " * 300 + "\n\n**next:** push.",
    )
    result = invoke_guard(stop_payload(transcript))
    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert "verbatim" not in parsed["reason"]
    assert "Load the humanize skill" in parsed["reason"]
