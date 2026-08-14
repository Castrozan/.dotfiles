import json
import os
import stat
import subprocess
from pathlib import Path


PI_MODULE_DIRECTORY = Path(__file__).resolve().parents[2]
EXTENSION_SOURCE = PI_MODULE_DIRECTORY / "extensions" / "human-facing-reply-guard.js"


def test_settled_reply_runs_the_shared_guard_and_requests_one_hidden_correction(
    tmp_path,
):
    dispatcher_record = tmp_path / "dispatcher-record.json"
    dispatcher = tmp_path / "dispatcher.py"
    dispatcher.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

payload = json.load(sys.stdin)
Path(os.environ["PI_DISPATCHER_RECORD"]).write_text(json.dumps(payload))
print(json.dumps({"decision": "block", "reason": "Rewrite the reply."}))
""",
        encoding="utf-8",
    )
    dispatcher.chmod(dispatcher.stat().st_mode | stat.S_IXUSR)

    extension = tmp_path / "human-facing-reply-guard.mjs"
    extension.write_text(
        EXTENSION_SOURCE.read_text(encoding="utf-8").replace(
            "@piHookDispatcher@", str(dispatcher)
        ),
        encoding="utf-8",
    )
    invocation = tmp_path / "invoke-extension.mjs"
    invocation.write_text(
        """const extensionSource = process.argv[2]
const handlers = new Map()
const sentMessages = []
const pi = {
  on: (event, handler) => handlers.set(event, handler),
  sendMessage: (message, options) => sentMessages.push({ message, options }),
}
const { default: loadExtension } = await import(extensionSource)
loadExtension(pi)
await handlers.get("message_end")({ message: { role: "user", content: [{ type: "text", text: "answer this" }] } })
await handlers.get("message_end")({ message: { role: "assistant", content: [{ type: "text", text: "Sure, done." }] } })
await handlers.get("agent_settled")()
await handlers.get("agent_settled")()
process.stdout.write(JSON.stringify(sentMessages))
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        ["node", str(invocation), extension.as_uri()],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PI_DISPATCHER_RECORD": str(dispatcher_record)},
    )

    assert json.loads(dispatcher_record.read_text(encoding="utf-8")) == {
        "hook_event_name": "Stop",
        "session_id": "pi-interactive-session",
        "user_request_text": "answer this",
        "reply_text": "Sure, done.",
    }
    assert json.loads(completed.stdout) == [
        {
            "message": {
                "customType": "human-facing-reply-format-guard",
                "content": "Rewrite the reply.",
                "display": False,
            },
            "options": {"triggerTurn": True, "deliverAs": "followUp"},
        }
    ]
