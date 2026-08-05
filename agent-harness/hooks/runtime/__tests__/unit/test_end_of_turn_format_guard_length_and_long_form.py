from end_of_turn_format_guard_test_support import (
    assistant_text_event,
    assistant_tool_use_event,
    invoke_guard,
    stop_payload,
    user_event,
    user_text_blocks_event,
    user_tool_result_event,
    write_transcript_from_events,
    write_transcript_with_final_assistant_reply,
    write_transcript_with_request_and_reply,
)


def test_allows_substantive_reply_above_the_old_one_hundred_fifty_word_cap(tmp_path):
    paragraph = " ".join(["word"] * 190)
    reply = f"{paragraph}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_reply_just_under_the_hard_word_ceiling(tmp_path):
    paragraph = " ".join(["word"] * 245)
    reply = f"{paragraph}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_long_form_document_reply_when_request_asked_for_one(tmp_path):
    document = "\n".join(
        [
            "Here is the full architecture overview you asked for.",
            "## Context",
            "- the system is a producer/consumer pipeline",
            "- the object store is the only integration seam",
        ]
        + [
            f"Paragraph {index} of detailed explanation at length."
            for index in range(40)
        ]
    )
    transcript = write_transcript_with_request_and_reply(
        tmp_path,
        "write me a full architecture overview of the platform, in detail",
        document,
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_long_prose_answer_when_request_says_in_detail(tmp_path):
    paragraph = " ".join(["word"] * 320)
    reply = f"{paragraph}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_request_and_reply(
        tmp_path, "explain in detail why the sync never ran on chise", reply
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_still_enforces_length_when_request_is_a_routine_question(tmp_path):
    paragraph = " ".join(["word"] * 320)
    reply = f"{paragraph}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_request_and_reply(
        tmp_path, "is obsidian syncing on chise?", reply
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() != ""


def test_grant_survives_a_tool_result_between_request_and_reply(tmp_path):
    paragraph = " ".join(["word"] * 320)
    reply = f"{paragraph}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_from_events(
        tmp_path,
        [
            user_event("write me a design doc for the reports service"),
            assistant_tool_use_event(),
            user_tool_result_event(),
            assistant_text_event(reply),
        ],
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_grant_reads_request_from_list_of_text_blocks(tmp_path):
    paragraph = " ".join(["word"] * 320)
    reply = f"{paragraph}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_from_events(
        tmp_path,
        [
            user_text_blocks_event("write me a design doc for the reports service"),
            assistant_tool_use_event(),
            assistant_text_event(reply),
        ],
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_reply_between_ten_and_fourteen_prose_lines(tmp_path):
    body = "\n".join(f"line {index} of the report" for index in range(10))
    reply = f"Opening answer line.\n{body}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""
