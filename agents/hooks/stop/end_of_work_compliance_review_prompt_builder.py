"""Build the user prompt sent to the haiku reviewer."""

import json

from end_of_work_compliance_review_workspace import MAX_DIFF_CHARS

MAX_USER_PROMPT_CHARS = 600

MAX_TOOL_CALL_INPUT_CHARS = 200

MAX_TOOL_CALLS_IN_PROMPT = 30

MAX_ASSISTANT_TEXT_CHARS = 1500


def summarize_tool_call_for_prompt(tool_call_block: dict) -> str:
    tool_name = tool_call_block.get("name", "?")
    tool_input = tool_call_block.get("input", {})

    if isinstance(tool_input, dict):
        if "file_path" in tool_input:
            return f"{tool_name}(file_path={tool_input['file_path']})"
        if "command" in tool_input:
            command_text = str(tool_input["command"])[:MAX_TOOL_CALL_INPUT_CHARS]
            return f"{tool_name}(command={command_text!r})"
        if "pattern" in tool_input:
            return f"{tool_name}(pattern={tool_input['pattern']!r})"
        if "url" in tool_input:
            return f"{tool_name}(url={tool_input['url']!r})"
        compact_input = json.dumps(tool_input)[:MAX_TOOL_CALL_INPUT_CHARS]
        return f"{tool_name}({compact_input})"

    return f"{tool_name}(...)"


MAX_PRIOR_ASSISTANT_TEXT_CHARS = 600


def format_tool_call_with_result(
    index: int, tool_call_block: dict, tool_results_by_use_id: dict[str, str]
) -> str:
    summary_line = f"{index + 1}. {summarize_tool_call_for_prompt(tool_call_block)}"
    tool_use_id = tool_call_block.get("id", "")
    result_text = tool_results_by_use_id.get(tool_use_id, "").strip()
    if not result_text:
        return summary_line
    return f"{summary_line}\n   -> result: {result_text}"


def build_review_user_prompt(
    current_turn_context: dict, workspace_policy_docs: dict[str, str], git_diff: str
) -> str:
    prompt_sections: list[str] = []

    if current_turn_context.get("prior_user_prompts"):
        prior_block = "\n\n".join(
            f"- {prompt_text[:MAX_USER_PROMPT_CHARS]}"
            for prompt_text in current_turn_context["prior_user_prompts"]
        )
        prompt_sections.append(f"## Earlier in this session (user)\n{prior_block}")

    if current_turn_context.get("prior_assistant_messages"):
        prior_assistant_block = "\n\n---\n\n".join(
            assistant_message[:MAX_PRIOR_ASSISTANT_TEXT_CHARS]
            for assistant_message in current_turn_context["prior_assistant_messages"]
        )
        prompt_sections.append(
            f"## Earlier in this session (agent text)\n{prior_assistant_block}"
        )

    if current_turn_context.get("current_user_prompts"):
        current_block = "\n\n".join(
            prompt_text[:MAX_USER_PROMPT_CHARS]
            for prompt_text in current_turn_context["current_user_prompts"]
        )
        prompt_sections.append(f"## User's request for this turn\n{current_block}")

    ordered_tool_calls = current_turn_context.get("ordered_tool_calls") or []
    tool_results_by_use_id = current_turn_context.get("tool_results_by_use_id") or {}
    if ordered_tool_calls:
        truncated_tool_calls = ordered_tool_calls[:MAX_TOOL_CALLS_IN_PROMPT]
        tool_lines = "\n".join(
            format_tool_call_with_result(index, tool_call, tool_results_by_use_id)
            for index, tool_call in enumerate(truncated_tool_calls)
        )
        overflow_note = ""
        if len(ordered_tool_calls) > MAX_TOOL_CALLS_IN_PROMPT:
            overflow_note = (
                f"\n... and {len(ordered_tool_calls) - MAX_TOOL_CALLS_IN_PROMPT} more"
            )
        prompt_sections.append(
            f"## Tool calls (in order, with truncated results)\n"
            f"{tool_lines}{overflow_note}"
        )

    assistant_text = current_turn_context.get("assistant_text", "")
    if assistant_text:
        prompt_sections.append(
            f"## Agent's final response (truncated)\n"
            f"{assistant_text[:MAX_ASSISTANT_TEXT_CHARS]}"
        )

    if workspace_policy_docs:
        doc_blocks = "\n\n".join(
            f"### {filename}\n{content}"
            for filename, content in workspace_policy_docs.items()
        )
        prompt_sections.append(f"## Workspace policy docs\n{doc_blocks}")

    if git_diff:
        prompt_sections.append(
            f"## Git diff (truncated to {MAX_DIFF_CHARS} chars)\n```\n{git_diff}\n```"
        )

    prompt_sections.append(
        "## Your task\n"
        "Apply each rule from your system prompt to this turn. "
        "Output one line per rule using the PASS/FAIL/UNKNOWN format. "
        "FAIL only when the diff or tool calls in this turn clearly trigger the "
        "violation; do not FAIL based on policy text alone, and treat tool "
        "results and the agent's text as evidence of what actually happened."
    )

    return "\n\n".join(prompt_sections)
