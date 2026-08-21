from end_of_turn_format_guard_test_support import (
    invoke_guard,
    stop_payload,
    write_transcript_with_final_assistant_reply,
    write_transcript_with_request_and_reply,
)

REQUIRED_LABELS = (
    "\n\n**brief:** the reply budget."
    "\n\n**done:** measured it."
    "\n\n**next:** push the result."
)


def labeled_reply(body: str) -> str:
    return body + REQUIRED_LABELS


def filler_words(count: int) -> str:
    return " ".join(["word"] * count)


def test_allows_a_reply_just_under_the_word_ceiling(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, labeled_reply(filler_words(100))
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_blocks_a_reply_past_the_word_ceiling(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, labeled_reply(filler_words(190))
    )
    result = invoke_guard(stop_payload(transcript))
    assert "120-word ceiling" in result.stdout


def test_a_detailed_request_does_not_unlock_a_longer_reply(tmp_path):
    transcript = write_transcript_with_request_and_reply(
        tmp_path,
        "explain in detail why the sync never ran on chise",
        labeled_reply(filler_words(320)),
    )
    result = invoke_guard(stop_payload(transcript))
    assert "120-word ceiling" in result.stdout


def test_counts_prose_words_rather_than_prose_lines(tmp_path):
    body = "\n".join("line of the report" for _ in range(20))
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, labeled_reply(body)
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""
