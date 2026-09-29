from end_of_turn_format_guard_test_support import (
    WELL_FORMED_REPLY,
    assistant_text_event,
    assistant_tool_use_event,
    invoke_guard,
    stop_payload,
    user_event,
    write_transcript_from_events,
    write_transcript_with_final_assistant_reply,
)
from human_facing_reply_test_support import reply_with_label_word_counts


def test_allows_well_formed_template_reply(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, WELL_FORMED_REPLY
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_clawde_background_agent_reply_that_would_otherwise_block(tmp_path):
    slop_reply = "You're right — fixed it.\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, slop_reply)
    result = invoke_guard(
        stop_payload(transcript),
        clawde_background_agent=True,
        clawde_marker_value="--continue",
    )
    assert result.stdout.strip() == ""


def test_allows_clawde_background_agent_reply_with_empty_marker_value(tmp_path):
    slop_reply = "You're right — fixed it.\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, slop_reply)
    result = invoke_guard(
        stop_payload(transcript),
        clawde_background_agent=True,
        clawde_marker_value="",
    )
    assert result.stdout.strip() == ""


def test_allows_an_extra_label_after_the_required_three(tmp_path):
    reply = (
        "evidence " * 80
        + "\n\n"
        + reply_with_label_word_counts(session=15, done=10, next_block=10)
        + "\n\n**Assumed:** bounded retries."
    )
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_fenced_mr_reference_without_a_link(tmp_path):
    reply = (
        "Here is the build log you asked for.\n"
        "```log\nbuild for MR !15 failed at step 3\n```\n"
        "**Done:** captured the log\n**Next:** nothing pending"
    )
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_benign_bang_number(tmp_path):
    reply = (
        "Traced the crash to the exit path.\n"
        "**Done:** the process exited with code !42 and left no leak.\n"
        "**Next:** nothing pending"
    )
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_a_hundred_word_confirmation(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, " ".join(["evidence"] * 100)
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_silent_when_stop_hook_already_active(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, "You're right, here is a long unstructured wall of slop text."
    )
    result = invoke_guard(stop_payload(transcript, stop_hook_active=True))
    assert result.stdout.strip() == ""


def test_silent_in_non_interactive_session(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, "You're right, here is a long unstructured wall of slop text."
    )
    result = invoke_guard(stop_payload(transcript), interactive=False)
    assert result.stdout.strip() == ""


def test_silent_on_non_stop_event(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, "You're right, here is a long unstructured wall of slop text."
    )
    payload = stop_payload(transcript)
    payload["hook_event_name"] = "SubagentStop"
    result = invoke_guard(payload)
    assert result.stdout.strip() == ""


def test_tool_use_only_final_turn_ignores_prior_violating_text(tmp_path):
    transcript = write_transcript_from_events(
        tmp_path,
        [
            user_event("first question"),
            assistant_text_event(
                "You're absolutely right, here is a long wall of slop."
            ),
            user_event("second question"),
            assistant_tool_use_event(),
        ],
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""
