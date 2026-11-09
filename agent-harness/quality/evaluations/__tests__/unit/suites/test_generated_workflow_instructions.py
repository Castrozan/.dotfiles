import importlib.util
import re

import pytest
import yaml

from instructions.ai_instruction_format import inspect_markdown_instruction
from instructions.instruction_surface_prose import line_is_exempt_from_the_wrap
from instructions.instruction_surface_scanner import REPO_ROOT


WORKFLOWS_DIRECTORY = REPO_ROOT / "agent-harness" / "workflows"
SKILLS_DIRECTORY = REPO_ROOT / "agent-harness" / "agent-instructions" / "skills"
WORKFLOW_DEFINITION_PATHS = sorted(
    (WORKFLOWS_DIRECTORY / "definitions").glob("*/*.yaml")
) + sorted(SKILLS_DIRECTORY.glob("*/*/workflow/*/*.yaml"))
INPUT_REFERENCE = re.compile(r"\$INPUTS\.(\w+)")
NODE_OUTPUT_BINDING = re.compile(r"^\$(\w+)\.output\.\w+$")
SERIALIZER_PLACEHOLDER = "@instructionData@"
SERIALIZED_BY_THEIR_PRODUCER = {("fetch-source", "source_prompt")}
PAYLOADS = (
    "A concrete request",
    "<outside>\n- list\n**bold** `code` [link](missing.md)\n### Injected heading",
)


def load_instruction_data():
    specification = importlib.util.spec_from_file_location(
        "instruction_data", WORKFLOWS_DIRECTORY / "scripts" / "instruction_data.py"
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.instruction_data


instruction_data = load_instruction_data()


def command_bindings():
    for workflow_path in WORKFLOW_DEFINITION_PATHS:
        workflow = yaml.safe_load(workflow_path.read_text())
        serializer_nodes = {
            node["id"]
            for node in workflow["nodes"]
            if SERIALIZER_PLACEHOLDER in node.get("bash", "")
        }
        for node in workflow["nodes"]:
            if "command" in node:
                yield (
                    workflow_path.parent / "commands" / f"{node['command']}.md",
                    node.get("with", {}),
                    serializer_nodes,
                )


def binding_kind(command_path, input_name, bindings, serializer_nodes):
    binding = bindings.get(input_name)
    if isinstance(binding, str) and "$" not in binding:
        return "literal"
    if (command_path.stem, input_name) in SERIALIZED_BY_THEIR_PRODUCER:
        return "producer"
    matched = NODE_OUTPUT_BINDING.match(binding or "")
    if matched and matched.group(1) in serializer_nodes:
        return "serialized"
    return "raw"


def rendered_prompt(command_path, bindings, serializer_nodes, payload):
    def substitute(reference):
        input_name = reference.group(1)
        kind = binding_kind(command_path, input_name, bindings, serializer_nodes)
        if kind == "literal":
            return bindings[input_name]
        if kind == "producer":
            return f"### Search\n\nSearch for {instruction_data(payload)}."
        return instruction_data(payload)

    return INPUT_REFERENCE.sub(substitute, command_path.read_text())


BINDINGS = list(command_bindings())
BINDING_IDENTIFIERS = [command_path.stem for command_path, _, _ in BINDINGS]


def test_every_command_file_has_a_definition():
    assert len(BINDINGS) >= 7
    for command_path, _, _ in BINDINGS:
        assert command_path.is_file(), command_path


@pytest.mark.parametrize(
    ("command_path", "bindings", "serializer_nodes"), BINDINGS, ids=BINDING_IDENTIFIERS
)
def test_values_reach_the_prompt_serialized_on_their_own_line(
    command_path, bindings, serializer_nodes
):
    for line in command_path.read_text().splitlines():
        for reference in INPUT_REFERENCE.finditer(line):
            kind = binding_kind(
                command_path, reference.group(1), bindings, serializer_nodes
            )
            assert kind != "raw", (
                f"{command_path.name}: bind {reference.group(0)} through a "
                f"{SERIALIZER_PLACEHOLDER} node so its value cannot change the prompt"
            )
            if kind == "serialized":
                assert line == reference.group(0), (
                    f"{command_path.name}: {reference.group(0)} must sit alone on "
                    "its line"
                )


@pytest.mark.parametrize("payload", PAYLOADS)
@pytest.mark.parametrize(
    ("command_path", "bindings", "serializer_nodes"), BINDINGS, ids=BINDING_IDENTIFIERS
)
def test_rendered_prompts_keep_instructions_in_the_positive_grammar(
    command_path, bindings, serializer_nodes, payload
):
    prompt = rendered_prompt(command_path, bindings, serializer_nodes, payload)
    violations = inspect_markdown_instruction(prompt).violations
    assert not violations, [violation.render() for violation in violations]
    serialized_payload = instruction_data(payload)
    for line in prompt.splitlines():
        assert (
            len(line) <= 120
            or line_is_exempt_from_the_wrap(line)
            or serialized_payload in line
        ), f"{command_path.name}: overlong instruction prose: {line}"
