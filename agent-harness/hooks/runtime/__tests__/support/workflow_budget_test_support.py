import json
import shutil
import subprocess

import pytest
from hook_module_loader import import_hyphenated_hook_module

subagent_spawn_budget_state = import_hyphenated_hook_module(
    "subagent_spawn_budget_state"
)
subagent_budget_guard_handler = import_hyphenated_hook_module(
    "subagent_budget_guard_handler"
)
workflow_script_budget_prelude = import_hyphenated_hook_module(
    "workflow_script_budget_prelude"
)
workflow_budget_guard_handler = import_hyphenated_hook_module(
    "workflow_budget_guard_handler"
)

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "AGENT_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_AGENT_NAME"
SESSION_UNDER_TEST = "session-under-test"

COUNTING_WORKFLOW_SCRIPT = """export const meta = {
  name: "counting",
  description: "a { brace } inside a string",
  phases: [{ title: "Count" }],
};
const results = [];
for (let attempt = 0; attempt < 5; attempt++) {
  try {
    results.push(await agent(`run the workflow (attempt ${attempt})`));
  } catch (refusal) {
    results.push("refused");
  }
}
return results;
"""


@pytest.fixture
def interactive_session_with_isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv(
        INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE,
        "/nix/store/interactive-communication.md",
    )
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, raising=False)
    monkeypatch.setenv(
        subagent_spawn_budget_state.STATE_DIRECTORY_OVERRIDE_ENVIRONMENT_VARIABLE,
        str(tmp_path / "state"),
    )
    return tmp_path


def workflow_hook_input(tool_input, working_directory="/nonexistent"):
    return {
        "tool_name": "Workflow",
        "session_id": SESSION_UNDER_TEST,
        "cwd": str(working_directory),
        "tool_input": tool_input,
    }


def agent_hook_input():
    return {
        "tool_name": "Agent",
        "session_id": SESSION_UNDER_TEST,
        "tool_input": {"description": "explore the module", "prompt": "do the work"},
    }


def guarded_script_of(result):
    assert result.decision is None
    assert set(result.updated_input) == {"script"}
    return result.updated_input["script"]


def run_guarded_script_under_node(guarded_script, output_tokens_per_agent=0):
    node_binary = shutil.which("node")
    if node_binary is None:
        pytest.skip("node is not on PATH")
    script_body = guarded_script.replace("export const meta", "const meta", 1)
    harness = f"""
let outputTokensSpent = 0;
globalThis.budget = {{ spent: () => outputTokensSpent }};
globalThis.log = () => {{}};
globalThis.agent = async (prompt) => {{
  outputTokensSpent += {output_tokens_per_agent};
  return "done";
}};
const AsyncFunction = Object.getPrototypeOf(async function () {{}}).constructor;
new AsyncFunction({json.dumps(script_body)})().then((results) => {{
  process.stdout.write(JSON.stringify(results));
}});
"""
    completed = subprocess.run(
        [node_binary, "-e", harness], capture_output=True, text=True, check=True
    )
    return json.loads(completed.stdout)
