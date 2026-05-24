"""Inspect the current turn's tool calls to decide whether the reviewer should run."""

PARKING_TOOL_NAMES = {"Monitor", "ScheduleWakeup"}


def has_any_file_mutating_tool_call(ordered_tool_calls: list[dict]) -> bool:
    mutating_tool_names = {"Edit", "Write", "NotebookEdit", "Update"}
    for tool_call_block in ordered_tool_calls:
        if tool_call_block.get("name") in mutating_tool_names:
            return True
    return False


def find_parking_tool_calls(ordered_tool_calls: list[dict]) -> list[dict]:
    parking_calls: list[dict] = []
    for tool_call_block in ordered_tool_calls:
        tool_name = tool_call_block.get("name", "")
        if tool_name in PARKING_TOOL_NAMES:
            parking_calls.append(tool_call_block)
            continue
        if tool_name == "Bash":
            tool_input = tool_call_block.get("input") or {}
            if tool_input.get("run_in_background") is True:
                parking_calls.append(tool_call_block)
    return parking_calls
