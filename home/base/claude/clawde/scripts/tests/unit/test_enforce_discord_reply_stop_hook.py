import importlib.util
import pathlib


def _load_hook_module():
    module_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent.parent
        / "channel-adapters"
        / "discord"
        / "scripts"
        / "enforce-discord-reply-stop-hook.py"
    )
    module_spec = importlib.util.spec_from_file_location(
        "enforce_discord_reply_stop_hook", module_path
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


hook = _load_hook_module()

DISCORD_ENVELOPE = (
    '<channel source="plugin:discord:discord" chat_id="555" '
    'message_id="1" user="lucas" ts="t">\nhello\n</channel>'
)


def _user(text):
    return {"type": "user", "message": {"content": text}}


def _assistant_reply(chat_id):
    return {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "name": "mcp__plugin_discord_discord__reply",
                    "input": {"chat_id": chat_id, "text": "hi"},
                }
            ]
        },
    }


def _assistant_text(text):
    return {
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": text}]},
    }


def test_blocks_when_discord_turn_has_no_reply():
    entries = [_user(DISCORD_ENVELOPE), _assistant_text("answered in terminal only")]
    assert hook.chat_id_needing_reply(entries, stop_hook_active=False) == "555"


def test_allows_when_reply_tool_was_called():
    entries = [_user(DISCORD_ENVELOPE), _assistant_reply("555")]
    assert hook.chat_id_needing_reply(entries, stop_hook_active=False) is None


def test_allows_non_discord_turn():
    entries = [_user("Heartbeat tick. Read HEARTBEAT.md."), _assistant_text("idle")]
    assert hook.chat_id_needing_reply(entries, stop_hook_active=False) is None


def test_fails_open_on_second_pass_to_avoid_infinite_loop():
    entries = [_user(DISCORD_ENVELOPE), _assistant_text("still no reply")]
    assert hook.chat_id_needing_reply(entries, stop_hook_active=True) is None


def test_enforces_reply_to_newest_discord_message_even_after_earlier_reply():
    entries = [
        _user(DISCORD_ENVELOPE),
        _assistant_reply("555"),
        _user(
            '<channel source="plugin:discord:discord" chat_id="777" '
            'message_id="2" user="lucas" ts="t">\nfollow up\n</channel>'
        ),
        _assistant_text("answered the new one in terminal"),
    ]
    assert hook.chat_id_needing_reply(entries, stop_hook_active=False) == "777"
