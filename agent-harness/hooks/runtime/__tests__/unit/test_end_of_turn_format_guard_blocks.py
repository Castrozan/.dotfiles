import json

from end_of_turn_format_guard_test_support import (
    assistant_text_event,
    invoke_guard,
    stop_payload,
    user_event,
    write_transcript_from_events,
    write_transcript_with_final_assistant_reply,
    write_transcript_with_request_and_reply,
)


def test_blocks_sycophancy_opener(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, "You're right to push. **Done:** fixed it\n**Next:** nothing pending"
    )
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_sure_opener(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, "Sure, done. **Done:** x\n**Next:** y"
    )
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_mechanics_narration_opener(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, "Let me re-read the code first.\n**Done:** x\n**Next:** y"
    )
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_em_dash_and_reason_names_the_violation(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, "State is fine — nothing to do.\n**Done:** x\n**Next:** y"
    )
    result = invoke_guard(stop_payload(transcript))
    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert parsed["reason"]
    assert "em dash" in parsed["reason"]


def test_blocks_long_reply_without_template_labels(tmp_path):
    long_unstructured = "\n".join(f"finding number {index}" for index in range(8))
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, long_unstructured
    )
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_long_prose_reply_even_with_template_labels(tmp_path):
    essay_lines = "\n".join(
        f"Sentence number {index} explaining yet another detail at length."
        for index in range(20)
    )
    wall = f"State sentence.\n{essay_lines}\n**Done:** x\n**Next:** done"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, wall)
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_genuine_wall_past_the_hard_word_ceiling(tmp_path):
    paragraph = " ".join(["word"] * 260)
    reply = f"{paragraph}\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert "hard ceiling" in parsed["reason"]


def test_blocks_em_dash_even_when_request_asks_for_a_document(tmp_path):
    reply = "Here is the design doc — section one follows.\n## Overview\nbody text."
    transcript = write_transcript_with_request_and_reply(
        tmp_path, "write me a design doc for the reports service", reply
    )
    result = invoke_guard(stop_payload(transcript))
    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert "em dash" in parsed["reason"]


def test_blocks_sycophancy_opener_even_when_request_asks_for_a_document(tmp_path):
    reply = (
        "Sure, here is the full architecture overview you asked for.\n## Context\nbody."
    )
    transcript = write_transcript_with_request_and_reply(
        tmp_path, "give me a full architecture overview of the platform", reply
    )
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_mr_without_link_even_when_request_asks_for_a_document(tmp_path):
    reply = (
        "Here is the design doc you asked for.\n"
        "## Overview\n"
        "The change landed as MR !15 with no link given here.\n"
        "More detail follows in the body."
    )
    transcript = write_transcript_with_request_and_reply(
        tmp_path, "write me a design doc for the reports service", reply
    )
    result = invoke_guard(stop_payload(transcript))
    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert "link" in parsed["reason"]


def test_blocks_multi_paragraph_dump_under_the_word_cap(tmp_path):
    reply = (
        "Opening paragraph that states the situation plainly.\n\n"
        "A second context paragraph that keeps explaining the background.\n\n"
        "**Done:** the first piece landed and was verified clean.\n\n"
        "A further paragraph piling on more detail about the work.\n\n"
        "**Next:** nothing pending"
    )
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert "paragraph" in parsed["reason"]


def test_blocks_bullet_list(tmp_path):
    reply = "Here is the state.\n**Done:** the work\n- first item\n- second item\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_numbered_list(tmp_path):
    reply = "Here is the state.\n**Done:** the work\n1. first step\n2. second step\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_section_header(tmp_path):
    reply = "Here is the state.\n## Root cause\nsome prose about it.\n**Done:** x\n**Next:** y"
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_blocks_mr_reference_without_a_link(tmp_path):
    reply = (
        "Landed the tidy on its branch.\n"
        "**Done:** committed as MR !15.\n"
        "**Next:** nothing pending"
    )
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"


def test_judges_final_reply_when_prior_turn_was_clean(tmp_path):
    transcript = write_transcript_from_events(
        tmp_path,
        [
            user_event("first question"),
            assistant_text_event("Committed as abc123 and rebuilt clean."),
            user_event("second question"),
            assistant_text_event("You're right to push. **Done:** x\n**Next:** y"),
        ],
    )
    result = invoke_guard(stop_payload(transcript))
    assert json.loads(result.stdout)["decision"] == "block"
