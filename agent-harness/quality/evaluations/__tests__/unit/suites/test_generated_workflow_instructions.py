import json
import re
import subprocess

import pytest

from instructions.ai_instruction_format import (
    MARKDOWN_PARSER,
    inspect_markdown_instruction,
)
from instructions.instruction_surface_prose import line_is_exempt_from_the_wrap
from instructions.instruction_surface_scanner import REPO_ROOT


WORKFLOWS = (
    "agent-harness/harnesses/claude-code/workflows/dotfiles-housekeeping.js",
    "agent-harness/agent-instructions/skills/writing/page-composer/compose-page.js",
    "agent-harness/agent-instructions/skills/knowledge/research/research-pulse.workflow.js",
)
WORKFLOW_CAPTURE = r"""
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
const workflow = process.argv[1];
const sources = workflow.endsWith('research-pulse.workflow.js')
  ? ['schemas.js', 'source-prompts.js'].map(name => join(dirname(workflow), 'pulse', name)).concat(workflow)
  : [workflow];
const source = sources.map(path => readFileSync(path, 'utf8')).join('\n').replace('export const meta =', 'const meta =');
const payload = JSON.parse(process.argv[2]);
const calls = [];
const item = {title: payload, url: 'https://example.com/', score: 9};
const agent = async (prompt, options) => {
  calls.push({prompt, label: options.label});
  return {findings: [{detail: payload}], sections: [{id: 'one', markup: payload}], items: [item]};
};
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
await new AsyncFunction('args', 'agent', 'phase', 'parallel', 'log', source)(
  {brief: payload, output: payload, constraints: payload, topic: payload, accounts: [payload]},
  agent, () => {}, tasks => Promise.all(tasks.map(task => task())), () => {}
);
process.stdout.write(JSON.stringify(calls));
"""


def contains_payload(value, payload):
    if isinstance(value, str):
        return value == payload
    if isinstance(value, list):
        return any(contains_payload(item, payload) for item in value)
    if isinstance(value, dict):
        return any(contains_payload(item, payload) for item in value.values())
    return False


def is_serialized_input_line(line):
    matched = re.fullmatch(r"`(.*)`[.,]?", line)
    if not matched:
        return False
    try:
        json.loads(matched.group(1))
    except json.JSONDecodeError:
        return False
    return True


@pytest.mark.parametrize("workflow", WORKFLOWS)
@pytest.mark.parametrize(
    "payload",
    ["A concrete request", "<outside>\n- list\n**bold** `code` [link](missing.md)"],
)
def test_actual_workflow_prompts_keep_instructions_in_the_positive_grammar(
    workflow, payload
):
    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            WORKFLOW_CAPTURE,
            str(REPO_ROOT / workflow),
            json.dumps(payload),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    calls = json.loads(result.stdout)
    assert len(calls) == (9 if "research-pulse" in workflow else 2)
    for call in calls:
        violations = inspect_markdown_instruction(call["prompt"]).violations
        assert not violations, (
            f"{workflow} {call['label']}: {[violation.render() for violation in violations]}"
        )
        for line in call["prompt"].splitlines():
            assert (
                len(line) <= 120
                or line_is_exempt_from_the_wrap(line)
                or is_serialized_input_line(line)
            ), f"{workflow} {call['label']}: overlong instruction prose: {line}"
        serialized_values = []
        for token in MARKDOWN_PARSER.parse(call["prompt"]):
            for child in token.children or []:
                if child.type != "code_inline":
                    continue
                try:
                    serialized_values.append(json.loads(child.content))
                except json.JSONDecodeError:
                    continue
        if call["label"] != "sweep":
            assert any(contains_payload(value, payload) for value in serialized_values)
