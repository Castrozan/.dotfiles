from end_of_turn_format_guard_test_support import (
    WELL_FORMED_REPLY,
    invoke_guard,
    stop_payload,
    write_transcript_with_final_assistant_reply,
)


def test_allows_every_humanize_visual_representation(tmp_path):
    visual_representations = (
        "```diff\n- old behavior\n+ new behavior\n```",
        "| Option | Scope |\n|---|---|\n| Automatic | Every system |",
        "```text\nState A -> State B\nState B -failure-> State A\n```",
        "```text\nClient -> API: request\nAPI -> Client: result\n```",
        "```text\nOwner\n├── Reader policy\n└── Hook mechanics\n```",
        "```text\n[Input] -> [Decision] -> [Output]\n```",
        "```text\nif eligible(system):\n    create_administrator(system)\n```",
    )

    for visual in visual_representations:
        transcript = write_transcript_with_final_assistant_reply(
            tmp_path, f"{WELL_FORMED_REPLY}\n{visual}"
        )
        result = invoke_guard(stop_payload(transcript))
        assert result.stdout.strip() == ""
