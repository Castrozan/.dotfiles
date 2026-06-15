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


def test_allows_full_template_with_three_bullets_each(tmp_path):
    reply = (
        "Wired the guard and verified the suite.\n"
        "**Done:**\n- rewrote the template\n- added the guard hook\n- registered it on Stop\n"
        "**Next:**\n- restart claude to pick up the env\n- tune caps if too strict\n"
        "- nothing else pending\n"
        "**Assumed:** single-bounce enforcement because you said inforce it"
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
