import re
from pathlib import Path

import pytest
import yaml

WORKFLOWS_DIRECTORY = Path(__file__).resolve().parents[2]
SKILLS_DIRECTORY = WORKFLOWS_DIRECTORY.parent / "agent-instructions" / "skills"
DEFINITIONS = sorted(
    [
        *WORKFLOWS_DIRECTORY.glob("definitions/*/*.yaml"),
        *SKILLS_DIRECTORY.glob("**/workflow/*/*.yaml"),
    ]
)
FIX_LOOP = WORKFLOWS_DIRECTORY / "definitions/dotfiles-fix-loop/dotfiles-fix-loop.yaml"
FIX_LOOP_MODEL_CALL_CEILING = 10
AI_NODE_KEYS = ("command", "prompt", "loop")
CONDITION = re.compile(r"^(\S+) (==|!=) '([^']*)'$")


def workflow(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def every_node(nodes: list[dict]) -> list[dict]:
    flattened = []
    for node in nodes:
        flattened.append(node)
        flattened.extend(every_node(node.get("loop_group", {}).get("nodes", [])))
    return flattened


def is_ai_node(node: dict) -> bool:
    return any(key in node for key in AI_NODE_KEYS)


def is_decision_node(node: dict) -> bool:
    return "@decide@" in node.get("bash", "")


def test_the_scan_finds_the_workflow_definitions():
    assert FIX_LOOP in DEFINITIONS and len(DEFINITIONS) >= 4


@pytest.mark.parametrize("path", DEFINITIONS, ids=lambda path: path.stem)
def test_every_ai_node_pins_its_model_and_effort(path):
    unpinned = [
        node["id"]
        for node in every_node(workflow(path)["nodes"])
        if is_ai_node(node) and not (node.get("model") and node.get("effort"))
    ]
    assert unpinned == []


def complementary(conditions: list[str]) -> bool:
    parsed = [CONDITION.match(condition or "") for condition in conditions]
    if len(parsed) != 2 or not all(parsed):
        return False
    first, second = (match.groups() for match in parsed)
    return first[0] == second[0] and first[2] == second[2] and first[1] != second[1]


def ai_calls_per_pass(nodes: list[dict]) -> int:
    ai_nodes = [node for node in nodes if is_ai_node(node)]
    exclusive = complementary([node.get("when") for node in ai_nodes])
    decisions = sum(map(is_decision_node, nodes))
    return (1 if exclusive else len(ai_nodes)) + decisions


def fix_loop_group() -> dict:
    return next(
        node["loop_group"]
        for node in workflow(FIX_LOOP)["nodes"]
        if "loop_group" in node
    )


def test_the_fix_loop_structure_caps_its_model_calls():
    nodes = workflow(FIX_LOOP)["nodes"]
    group = fix_loop_group()
    outside = [node for node in nodes if "loop_group" not in node]
    ceiling = group["max_iterations"] * ai_calls_per_pass(group["nodes"])
    ceiling += ai_calls_per_pass(outside)
    assert ceiling <= FIX_LOOP_MODEL_CALL_CEILING


def test_the_next_step_guard_shares_the_loop_cap():
    group = fix_loop_group()
    decision = next(node for node in group["nodes"] if is_decision_node(node))
    cap = re.search(r"--max-iterations (\d+)", decision["bash"])
    assert cap and int(cap.group(1)) == group["max_iterations"]
