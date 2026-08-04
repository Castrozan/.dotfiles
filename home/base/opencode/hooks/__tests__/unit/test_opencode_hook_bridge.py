import json
import os
import stat
import subprocess
from pathlib import Path


HOOK_BRIDGE_SOURCE = Path(__file__).resolve().parents[2] / "opencode-hook-bridge.js"


def write_hook_dispatcher_launcher(tmp_path):
    launcher_path = tmp_path / "hook-dispatcher-launcher.py"
    launcher_path.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

payload = json.load(sys.stdin)
record_path = Path(os.environ[\"OPENCODE_HOOK_RECORD\"])
try:
    records = json.loads(record_path.read_text(encoding=\"utf-8\"))
except OSError:
    records = []
records.append({\"dispatcher\": sys.argv[1], \"payload\": payload})
record_path.write_text(json.dumps(records), encoding=\"utf-8\")
responses = json.loads(os.environ[\"OPENCODE_HOOK_RESPONSES\"])
response = responses.get(sys.argv[1], os.environ.get(\"OPENCODE_HOOK_RESPONSE\", \"\"))
if response:
    print(response if isinstance(response, str) else json.dumps(response))
""",
        encoding="utf-8",
    )
    launcher_path.chmod(launcher_path.stat().st_mode | stat.S_IXUSR)
    return launcher_path


def invoke_hook_bridge(
    tmp_path,
    dispatcher_response,
    hook_name,
    hook_input,
    hook_output,
    dispatcher_responses=None,
):
    launcher_path = write_hook_dispatcher_launcher(tmp_path)
    record_path = tmp_path / "hook-dispatcher-record.json"
    hook_bridge_path = tmp_path / "opencode-hook-bridge.js"
    hook_bridge_path.write_text(
        HOOK_BRIDGE_SOURCE.read_text(encoding="utf-8").replace(
            "@opencodeHookDispatcher@", str(launcher_path)
        ),
        encoding="utf-8",
    )
    invocation_path = tmp_path / "invoke-hook-bridge.mjs"
    invocation_path.write_text(
        """const [hookBridgeSource, scenarioSource] = process.argv.slice(2)
const scenario = JSON.parse(scenarioSource)
const { OpenCodeHookBridge } = await import(hookBridgeSource)
const hooks = await OpenCodeHookBridge({ directory: scenario.directory })
const originalToolArguments = scenario.hookOutput.args

try {
  await hooks[scenario.hookName](scenario.hookInput, scenario.hookOutput)
  process.stdout.write(
    JSON.stringify({
      hookOutput: scenario.hookOutput,
      originalToolArgumentsWereRetained: originalToolArguments === scenario.hookOutput.args,
    }),
  )
} catch (error) {
  process.stdout.write(
    JSON.stringify({
      hookOutput: scenario.hookOutput,
      originalToolArgumentsWereRetained: originalToolArguments === scenario.hookOutput.args,
      error: error.message,
    }),
  )
}
""",
        encoding="utf-8",
    )
    scenario = {
        "directory": "/workspace/project",
        "hookName": hook_name,
        "hookInput": hook_input,
        "hookOutput": hook_output,
    }
    result = subprocess.run(
        [
            "node",
            "--experimental-default-type=module",
            str(invocation_path),
            hook_bridge_path.as_uri(),
            json.dumps(scenario),
        ],
        capture_output=True,
        text=True,
        check=True,
        env={
            **os.environ,
            "OPENCODE_HOOK_RECORD": str(record_path),
            "OPENCODE_HOOK_RESPONSE": json.dumps(dispatcher_response),
            "OPENCODE_HOOK_RESPONSES": json.dumps(dispatcher_responses or {}),
        },
    )
    records = (
        json.loads(record_path.read_text(encoding="utf-8"))
        if record_path.exists()
        else []
    )
    return json.loads(result.stdout), records


def only_dispatcher_record(records):
    assert len(records) == 1
    return records[0]


def test_pre_tool_hook_denies_a_normalized_bash_command(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": "git add . is prohibited",
            }
        },
        "tool.execute.before",
        {"tool": "bash", "sessionID": "ses-1", "callID": "call-1"},
        {"args": {"command": "git add ."}},
    )

    assert result["error"] == "git add . is prohibited"
    record = only_dispatcher_record(records)
    assert record == {
        "dispatcher": "pre-tool-use-dispatcher.py",
        "payload": {
            "hook_event_name": "PreToolUse",
            "session_id": "ses-1",
            "cwd": "/workspace/project",
            "tool_name": "Bash",
            "tool_input": {"command": "git add ."},
        },
    }


def test_pre_tool_hook_applies_updated_input_with_opencode_argument_names(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "permissionDecision": "allow",
                "updatedInput": {
                    "file_path": "src/example.py",
                    "old_string": "before",
                    "new_string": "after",
                },
            }
        },
        "tool.execute.before",
        {"tool": "edit", "sessionID": "ses-2", "callID": "call-2"},
        {
            "args": {
                "filePath": "src/example.py",
                "oldString": "before",
                "newString": "after",
            }
        },
    )

    assert "error" not in result
    assert result["hookOutput"]["args"] == {
        "filePath": "src/example.py",
        "oldString": "before",
        "newString": "after",
    }
    assert result["originalToolArgumentsWereRetained"]
    record = only_dispatcher_record(records)
    assert record["payload"]["tool_name"] == "Edit"
    assert record["payload"]["tool_input"] == {
        "file_path": "src/example.py",
        "old_string": "before",
        "new_string": "after",
    }


def test_post_tool_hook_adds_dispatcher_guidance_to_tool_output(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "systemMessage": "MANDATORY: config.nix changed.",
            "hookSpecificOutput": {
                "additionalContext": "Run rebuild before responding."
            },
        },
        "tool.execute.after",
        {
            "tool": "write",
            "sessionID": "ses-3",
            "callID": "call-3",
            "args": {"filePath": "config.nix", "content": "{}"},
        },
        {"title": "Write", "output": "Wrote config.nix", "metadata": {}},
        dispatcher_responses={"stop-dispatcher.py": {}},
    )

    assert "error" not in result
    assert result["hookOutput"]["output"] == (
        "Wrote config.nix\n\nMANDATORY: config.nix changed.\n\n"
        "Run rebuild before responding."
    )
    assert [record["dispatcher"] for record in records] == [
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
    ]
    assert records[0]["payload"]["tool_name"] == "Write"
    assert records[0]["payload"]["tool_input"] == {
        "file_path": "config.nix",
        "content": "{}",
    }


def test_user_prompt_hook_adds_dispatcher_context_to_the_prompt_text(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "additionalContext": "Use the enforced reply template."
            }
        },
        "chat.message",
        {"sessionID": "ses-4"},
        {
            "message": {"id": "msg-4"},
            "parts": [
                {
                    "id": "prt-4",
                    "sessionID": "ses-4",
                    "messageID": "msg-4",
                    "type": "text",
                    "text": "Continue",
                }
            ],
        },
    )

    assert "error" not in result
    assert result["hookOutput"]["parts"][0]["text"] == (
        "Continue\n\nUse the enforced reply template."
    )
    record = only_dispatcher_record(records)
    assert record == {
        "dispatcher": "user-prompt-submit-dispatcher.py",
        "payload": {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "ses-4",
            "cwd": "/workspace/project",
        },
    }


def test_compaction_hook_adds_dispatcher_context_to_the_compaction_prompt(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "additionalContext": "Re-read the active deep-work tracker."
            }
        },
        "experimental.session.compacting",
        {"sessionID": "ses-5"},
        {"context": [], "prompt": None},
    )

    assert "error" not in result
    assert result["hookOutput"]["context"] == ["Re-read the active deep-work tracker."]
    record = only_dispatcher_record(records)
    assert record == {
        "dispatcher": "session-start-dispatcher.py",
        "payload": {
            "hook_event_name": "SessionStart",
            "session_id": "ses-5",
            "source": "compact",
            "cwd": "/workspace/project",
        },
    }


def test_pre_tool_hook_translates_the_opencode_skill_name(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": "blocked skill",
            }
        },
        "tool.execute.before",
        {"tool": "skill", "sessionID": "ses-6", "callID": "call-6"},
        {"args": {"name": "claude-api"}},
    )

    assert result["error"] == "blocked skill"
    assert only_dispatcher_record(records)["payload"]["tool_input"] == {
        "skill": "claude-api"
    }


def test_post_tool_hook_rejects_a_blocking_dispatcher_decision(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {"decision": "block", "reason": "Split the file before continuing."},
        "tool.execute.after",
        {
            "tool": "write",
            "sessionID": "ses-7",
            "callID": "call-7",
            "args": {"filePath": "large.py", "content": ""},
        },
        {"title": "Write", "output": "Wrote large.py", "metadata": {}},
    )

    assert result["error"] == "Split the file before continuing."
    assert (
        only_dispatcher_record(records)["dispatcher"] == "post-tool-use-dispatcher.py"
    )


def test_post_tool_hook_runs_the_turn_review_dispatcher(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {"systemMessage": "MANDATORY: config.nix changed."},
        "tool.execute.after",
        {
            "tool": "write",
            "sessionID": "ses-8",
            "callID": "call-8",
            "args": {"filePath": "module.py", "content": "value = 1\n"},
        },
        {"title": "Write", "output": "Wrote module.py", "metadata": {}},
        dispatcher_responses={
            "stop-dispatcher.py": {"systemMessage": "Run ruff before pushing."}
        },
    )

    assert "error" not in result
    assert result["hookOutput"]["output"] == (
        "Wrote module.py\n\nMANDATORY: config.nix changed.\n\nRun ruff before pushing."
    )
    assert [record["dispatcher"] for record in records] == [
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
    ]


def test_file_only_prompt_defers_context_injection_until_a_text_prompt(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "additionalContext": "Use the enforced reply template."
            }
        },
        "chat.message",
        {"sessionID": "ses-9"},
        {
            "message": {"id": "msg-9"},
            "parts": [
                {
                    "id": "prt-9",
                    "sessionID": "ses-9",
                    "messageID": "msg-9",
                    "type": "file",
                    "mime": "image/png",
                    "url": "file:///tmp/example.png",
                }
            ],
        },
    )

    assert "error" not in result
    assert records == []
