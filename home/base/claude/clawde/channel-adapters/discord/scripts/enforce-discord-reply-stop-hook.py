import json
import re
import sys

DISCORD_CHANNEL_ENVELOPE_PATTERN = re.compile(
    r'<channel source="plugin:discord:discord"[^>]*\bchat_id="([^"]+)"'
)
DISCORD_REPLY_TOOL_NAME = "mcp__plugin_discord_discord__reply"


def message_content_as_text(transcript_entry):
    message = transcript_entry.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return json.dumps(content, ensure_ascii=False)
    return ""


def latest_discord_turn_index_and_chat_id(transcript_entries):
    for index in range(len(transcript_entries) - 1, -1, -1):
        entry = transcript_entries[index]
        if entry.get("type") != "user":
            continue
        match = DISCORD_CHANNEL_ENVELOPE_PATTERN.search(message_content_as_text(entry))
        if match:
            return index, match.group(1)
    return None, None


def discord_reply_called_after(transcript_entries, turn_index):
    for entry in transcript_entries[turn_index + 1 :]:
        if entry.get("type") != "assistant":
            continue
        content = entry.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == DISCORD_REPLY_TOOL_NAME
            ):
                return True
    return False


def chat_id_needing_reply(transcript_entries, stop_hook_active):
    turn_index, chat_id = latest_discord_turn_index_and_chat_id(transcript_entries)
    if turn_index is None:
        return None
    if discord_reply_called_after(transcript_entries, turn_index):
        return None
    if stop_hook_active:
        return None
    return chat_id


def read_transcript_entries(transcript_path):
    entries = []
    try:
        with open(transcript_path) as transcript_file:
            for line in transcript_file:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entries.append(json.loads(stripped))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    transcript_path = hook_input.get("transcript_path")
    if not transcript_path:
        sys.exit(0)
    chat_id = chat_id_needing_reply(
        read_transcript_entries(transcript_path),
        bool(hook_input.get("stop_hook_active")),
    )
    if chat_id is None:
        sys.exit(0)
    reason = (
        "You have not delivered your response to Discord. Terminal output never reaches "
        f"the user. Call the reply tool ({DISCORD_REPLY_TOOL_NAME}) with chat_id "
        f"{chat_id} and your full response now, then stop."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
