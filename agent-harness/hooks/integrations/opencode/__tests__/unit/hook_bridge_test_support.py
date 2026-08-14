import json
import os
import stat
import subprocess
from pathlib import Path


HOOK_BRIDGE_SOURCE_DIRECTORY = Path(__file__).resolve().parents[2] / "hook-bridge"
HOOK_BRIDGE_ENTRY_FILENAME = "opencode-hook-bridge.js"


def write_hook_bridge_sources(tmp_path, launcher_path):
    for source_path in HOOK_BRIDGE_SOURCE_DIRECTORY.glob("*.js"):
        (tmp_path / source_path.name).write_text(
            source_path.read_text(encoding="utf-8").replace(
                "@opencodeHookDispatcher@", str(launcher_path)
            ),
            encoding="utf-8",
        )
    return tmp_path / HOOK_BRIDGE_ENTRY_FILENAME


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


def invoke_hook_bridge_sequence(
    tmp_path,
    dispatcher_response,
    hook_calls,
    dispatcher_responses=None,
    session_messages=None,
):
    launcher_path = write_hook_dispatcher_launcher(tmp_path)
    record_path = tmp_path / "hook-dispatcher-record.json"
    hook_bridge_path = write_hook_bridge_sources(tmp_path, launcher_path)
    invocation_path = tmp_path / "invoke-hook-bridge.mjs"
    invocation_path.write_text(
        """const [hookBridgeSource, scenarioSource] = process.argv.slice(2)
const scenario = JSON.parse(scenarioSource)
const promptAsyncCalls = []
let currentSessionMessages = scenario.sessionMessages ?? []
const client = {
  session: {
    messages: async () => ({ data: currentSessionMessages }),
    promptAsync: async (options) => {
      promptAsyncCalls.push(options)
      return { data: undefined }
    },
  },
}
const { OpenCodeHookBridge } = await import(hookBridgeSource)
const hooks = await OpenCodeHookBridge({ directory: scenario.directory, client })
const results = []

for (const hookCall of scenario.hookCalls) {
  if (Array.isArray(hookCall.sessionMessages)) {
    currentSessionMessages = hookCall.sessionMessages
  }
  const originalToolArguments = hookCall.hookOutput.args
  const result = { hookOutput: hookCall.hookOutput }
  try {
    await hooks[hookCall.hookName](hookCall.hookInput, hookCall.hookOutput)
  } catch (error) {
    result.error = error.message
  }
  result.originalToolArgumentsWereRetained =
    originalToolArguments === hookCall.hookOutput.args
  result.promptAsyncCalls = [...promptAsyncCalls]
  results.push(result)
}
process.stdout.write(JSON.stringify(results))
""",
        encoding="utf-8",
    )
    scenario = {
        "directory": "/workspace/project",
        "hookCalls": hook_calls,
        "sessionMessages": session_messages or [],
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


def invoke_hook_bridge(
    tmp_path,
    dispatcher_response,
    hook_name,
    hook_input,
    hook_output,
    dispatcher_responses=None,
    session_messages=None,
):
    results, records = invoke_hook_bridge_sequence(
        tmp_path,
        dispatcher_response,
        [
            {
                "hookName": hook_name,
                "hookInput": hook_input,
                "hookOutput": hook_output,
            }
        ],
        dispatcher_responses,
        session_messages,
    )
    return results[0], records


def only_dispatcher_record(records):
    assert len(records) == 1
    return records[0]
