import json
import os
import stat
import subprocess
import sys
from pathlib import Path


HOOK_BRIDGE_SOURCE_DIRECTORY = Path(__file__).resolve().parents[2] / "hook-bridge"
HOOK_BRIDGE_ENTRY_FILENAME = "server.js"


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
        f"#!{sys.executable}\n"
        """import json
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


def invoke_hook_bridge_sequence(tmp_path, dispatcher_response, hook_calls):
    launcher = write_hook_dispatcher_launcher(tmp_path)
    record_path = tmp_path / "hook-dispatcher-record.json"
    bridge = write_hook_bridge_sources(tmp_path, launcher)
    invocation = tmp_path / "invoke-hook-bridge.mjs"
    invocation.write_text(
        """const [source, serialized] = process.argv.slice(2)
const scenario = JSON.parse(serialized)
const hooks = new Map()
const syntheticCalls = []
const queue = []
let wake
const context = {
  location: { directory: '/workspace/project' },
  tool: { hook: async (name, callback) => hooks.set('tool.' + name, callback) },
  session: {
    hook: async (name, callback) => hooks.set('session.' + name, callback),
    synthetic: async (input) => syntheticCalls.push(input),
  },
  event: {
    async *subscribe({ signal }) {
      signal.addEventListener('abort', () => wake?.(), { once: true })
      while (!signal.aborted) {
        if (!queue.length) await new Promise(resolve => { wake = resolve })
        if (signal.aborted) return
        const item = queue.shift()
        yield item.event
        item.processed()
      }
    },
  },
}
const plugin = (await import(source)).default
if (plugin.id !== 'dotfiles.hook-bridge') throw new Error('Missing plugin identity')
const cleanup = await plugin.setup(context)
const results = []
for (const call of scenario) {
  const originalInput = call.event.input
  const result = { event: call.event }
  try {
    if (call.hookName === 'event') {
      await new Promise(processed => {
        queue.push({ event: call.event, processed })
        wake?.()
      })
    } else {
      await hooks.get(call.hookName)(call.event)
    }
  } catch (failure) {
    result.error = failure.message
  }
  result.originalToolArgumentsWereRetained = originalInput === call.event.input
  result.syntheticCalls = [...syntheticCalls]
  results.push(result)
}
await cleanup()
process.stdout.write(JSON.stringify(results))
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "node",
            "--experimental-default-type=module",
            str(invocation),
            bridge.as_uri(),
            json.dumps(hook_calls),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
        env=os.environ
        | {
            "OPENCODE_HOOK_RECORD": str(record_path),
            "OPENCODE_HOOK_RESPONSE": json.dumps(dispatcher_response),
            "OPENCODE_HOOK_RESPONSES": "{}",
        },
    )
    records = json.loads(record_path.read_text()) if record_path.exists() else []
    return json.loads(result.stdout), records


def invoke_hook_bridge(tmp_path, dispatcher_response, hook_name, event):
    results, records = invoke_hook_bridge_sequence(
        tmp_path, dispatcher_response, [{"hookName": hook_name, "event": event}]
    )
    return results[0], records


def only_dispatcher_record(records):
    assert len(records) == 1
    return records[0]
