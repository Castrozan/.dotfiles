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


def test_allows_well_formed_template_reply(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, WELL_FORMED_REPLY
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_prose_with_done_next_and_assumed(tmp_path):
    reply = (
        "Wired the guard and verified the whole suite passes after the rebuild.\n"
        "**Done:** rewrote the template into prose, added the guard hook, and registered it on "
        "the Stop event so it runs at the end of every interactive turn.\n"
        "**Next:** restart claude to pick up the change, then tune the caps later if they bite.\n"
        "**Assumed:** single-bounce enforcement because you asked to inforce it."
    )
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_reply_at_the_word_cap(tmp_path):
    paragraph = " ".join(["word"] * 246)
    reply = f"{paragraph}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_mr_reference_with_a_link(tmp_path):
    reply = (
        "Landed the tidy on its branch.\n"
        "**Done:** committed as MR !15, "
        "https://gitlab.example.com/group/repo/-/merge_requests/15.\n"
        "**Next:** nothing pending"
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


def test_allows_short_one_line_confirmation(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, "Committed as abc123 and rebuilt clean."
    )
    result = invoke_guard(stop_payload(transcript))
    assert result.stdout.strip() == ""


def test_allows_code_block_without_counting_fenced_lines(tmp_path):
    fenced = "\n".join(f"line {index}" for index in range(30))
    reply = (
        "Here is the script you asked for.\n"
        f"```python\n{fenced}\n```\n"
        "**Done:** wrote it\n**Next:** run it"
    )
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
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


def test_scopes_to_current_turn_ignoring_prior_violating_text(tmp_path):
    transcript = write_transcript_from_events(
        tmp_path,
        [
            user_event("first question"),
            assistant_text_event(
                "You're absolutely right, here is a long wall of slop."
            ),
            user_event("second question"),
            assistant_text_event("Committed as abc123 and rebuilt clean."),
        ],
    )
    result = invoke_guard(stop_payload(transcript))
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
