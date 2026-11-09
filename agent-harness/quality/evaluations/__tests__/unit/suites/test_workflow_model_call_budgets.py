import importlib.util
import re

import yaml

from instructions.instruction_surface_scanner import REPO_ROOT


SKILLS_DIRECTORY = REPO_ROOT / "agent-harness" / "agent-instructions" / "skills"
WORKFLOW_DEFINITION_PATHS = sorted(
    (REPO_ROOT / "agent-harness" / "workflows" / "definitions").glob("*/*.yaml")
) + sorted(SKILLS_DIRECTORY.glob("*/*/workflow/*/*.yaml"))
WORKFLOW_BUDGET_GUARD_HANDLER_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "hooks"
    / "runtime"
    / "pre-tool-use"
    / "subagent-budget-guard"
    / "workflow_budget_guard_handler.py"
)
HOUSEKEEPING_SLICER_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "workflows"
    / "definitions"
    / "dotfiles-housekeeping"
    / "scripts"
    / "dotfiles_housekeeping_slices.py"
)
HOUSEKEEPING_CANDIDATES_PATH = (
    HOUSEKEEPING_SLICER_PATH.parent / "housekeeping_candidates.py"
)
RESEARCH_SOURCES_PATH = (
    SKILLS_DIRECTORY
    / "knowledge"
    / "research"
    / "workflow"
    / "research-pulse"
    / "scripts"
    / "research_pulse_sources.py"
)
MAXIMUM_MODEL_CALLS_PER_ROUTINE_WORKFLOW = 2
MAXIMUM_RESEARCH_SOURCE_CALLS = 7
MODEL_TIERS = {"small", "medium", "large"}
SUPPORTED_EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}
MODEL_NODE_KEYS = {"prompt", "command", "loop", "loop_group"}


def load_workflows():
    return {
        path.stem: yaml.safe_load(path.read_text())
        for path in WORKFLOW_DEFINITION_PATHS
    }


def model_nodes(workflow):
    return [node for node in workflow["nodes"] if MODEL_NODE_KEYS & node.keys()]


def fan_out_nodes(workflow):
    return [node for node in workflow["nodes"] if "fan_out" in node]


def total_model_calls(workflows, workflow_name):
    workflow = workflows[workflow_name]
    return len(model_nodes(workflow)) + sum(
        total_model_calls(workflows, node["workflow"])
        for node in workflow["nodes"]
        if "workflow" in node and "fan_out" not in node
    )


def declared_integer(path, constant_name):
    return int(re.search(rf"\b{constant_name} = ([0-9_]+)", path.read_text()).group(1))


def test_every_workflow_definition_is_discovered():
    assert {
        "dotfiles-housekeeping",
        "dotfiles-housekeeping-slice",
        "dotfiles-housekeeping-verify",
        "compose-page",
        "research-pulse",
        "research-pulse-fetch",
    } <= load_workflows().keys()


def test_every_model_call_pins_a_portable_tier_and_an_effort():
    for name, workflow in load_workflows().items():
        for node in model_nodes(workflow):
            assert node.get("model") in MODEL_TIERS, (
                f"{name}/{node['id']} must pin a small, medium, or large tier so every "
                "harness resolves it to its own model instead of the caller's"
            )
            assert node.get("effort") in SUPPORTED_EFFORT_LEVELS, (
                f"{name}/{node['id']} must pin its effort; an unpinned call costs "
                "whatever its invoker happened to be set to"
            )
            assert "output_format" in node, (
                f"{name}/{node['id']} must declare the shape it hands downstream"
            )


def test_every_workflow_is_read_only_and_runs_in_place():
    for name, workflow in load_workflows().items():
        assert workflow.get("mutates_checkout") is False, name
        assert workflow.get("worktree") == {"enabled": False}, name
        for node in workflow["nodes"]:
            if "workflow" not in node:
                assert node.get("mutates_checkout") is False, f"{name}/{node['id']}"


def test_fan_out_runs_only_over_deterministic_lists():
    for name, workflow in load_workflows().items():
        producers = {node["id"]: node for node in workflow["nodes"]}
        for node in fan_out_nodes(workflow):
            source_node = re.match(r"\$(\w+)\.output", node["fan_out"]["items"])
            assert source_node, f"{name}/{node['id']} fans out over a non-node value"
            assert "bash" in producers[source_node.group(1)], (
                f"{name}/{node['id']} fans out over model-produced data"
            )


def test_the_routine_workflow_stays_within_its_model_call_budget():
    workflows = load_workflows()
    compose_page = workflows["compose-page"]
    assert not fan_out_nodes(compose_page)
    assert (
        total_model_calls(workflows, "compose-page")
        <= MAXIMUM_MODEL_CALLS_PER_ROUTINE_WORKFLOW
    )


def test_housekeeping_fits_its_fan_out_under_the_orchestrated_ceiling():
    workflows = load_workflows()
    orchestrated_agent_ceiling = declared_integer(
        WORKFLOW_BUDGET_GUARD_HANDLER_PATH, "ORCHESTRATED_WORKFLOW_AGENT_CEILING"
    )
    readers_per_slice = total_model_calls(workflows, "dotfiles-housekeeping-slice")
    calls_per_batch = total_model_calls(workflows, "dotfiles-housekeeping-verify")
    maximum_calls = (
        total_model_calls(workflows, "dotfiles-housekeeping")
        + readers_per_slice
        * declared_integer(HOUSEKEEPING_SLICER_PATH, "MAXIMUM_SLICES")
        + calls_per_batch
        * declared_integer(HOUSEKEEPING_CANDIDATES_PATH, "VERIFIER_COUNT")
    )
    assert maximum_calls <= orchestrated_agent_ceiling


def test_the_research_fanout_is_bounded_by_its_source_list():
    workflows = load_workflows()
    specification = importlib.util.spec_from_file_location(
        "research_pulse_sources", RESEARCH_SOURCES_PATH
    )
    research_sources = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(research_sources)
    source_count = len(list(research_sources.source_definitions("topic", ["account"])))
    assert 0 < source_count <= MAXIMUM_RESEARCH_SOURCE_CALLS
    assert total_model_calls(workflows, "research-pulse-fetch") == 1
    assert total_model_calls(workflows, "research-pulse") == 2
