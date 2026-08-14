import re

from instruction_surface_scanner import REPO_ROOT


DOTFILES_WORKFLOW_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "harnesses" / "claude-code" / "workflows"
)
PAGE_COMPOSER_WORKFLOW_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "page-composer"
    / "compose-page.js"
)
RESEARCH_PULSE_WORKFLOW_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "research"
    / "research-pulse.workflow.js"
)
MAXIMUM_MODEL_CALLS_PER_ROUTINE_WORKFLOW = 2
MAXIMUM_TURNS_PER_ROUTINE_MODEL_CALL = 8
MAXIMUM_RESEARCH_SOURCE_CALLS = 7


def routine_workflow_paths():
    return sorted(DOTFILES_WORKFLOW_DIRECTORY.glob("dotfiles-*.js")) + [
        PAGE_COMPOSER_WORKFLOW_PATH
    ]


def test_routine_workflows_stay_within_their_model_call_budget():
    for workflow_path in routine_workflow_paths():
        source = workflow_path.read_text()
        model_call_count = len(re.findall(r"\bagent\s*\(", source))
        maximum_turns = [int(value) for value in re.findall(r"maxTurns: (\d+)", source)]
        assert model_call_count <= MAXIMUM_MODEL_CALLS_PER_ROUTINE_WORKFLOW, (
            f"{workflow_path.name} declares {model_call_count} agent call sites; routine "
            f"workflows may declare at most {MAXIMUM_MODEL_CALLS_PER_ROUTINE_WORKFLOW}"
        )
        assert len(maximum_turns) == model_call_count
        assert all(
            value <= MAXIMUM_TURNS_PER_ROUTINE_MODEL_CALL for value in maximum_turns
        )
        assert "parallel(" not in source, (
            f"{workflow_path.name} uses parallel fan-out instead of its fixed call budget"
        )
        assert "pipeline(" not in source, (
            f"{workflow_path.name} uses pipeline fan-out instead of its fixed call budget"
        )
        for dynamic_call_pattern in (
            "for (",
            "for await (",
            "while (",
            ".forEach(",
            "Promise.all(",
        ):
            assert dynamic_call_pattern not in source, (
                f"{workflow_path.name} uses {dynamic_call_pattern} around a routine "
                "workflow; keep model-call control flow visibly fixed"
            )
        first_map_position = source.find(".map(")
        last_model_call_position = source.rfind("agent(")
        assert (
            first_map_position == -1 or first_map_position > last_model_call_position
        ), f"{workflow_path.name} maps data before its final agent call"


def test_the_explicit_research_fanout_pins_every_call_to_a_bounded_model():
    source = RESEARCH_PULSE_WORKFLOW_PATH.read_text()
    model_call_count = len(re.findall(r"\bagent\s*\(", source))
    pinned_call_count = len(
        re.findall(r'boundedAgentOptions\([^)]*, "(?:haiku|sonnet)"', source)
    )
    assert pinned_call_count == model_call_count
    assert "  model," in source
    maximum_turns = [int(value) for value in re.findall(r"maxTurns: (\d+)", source)]
    assert maximum_turns == [8]
    sources = source.split("const SOURCES = [", 1)[1].split("];", 1)[0]
    source_call_count = len(re.findall(r'^    key: "', sources, re.MULTILINE))
    assert source_call_count <= MAXIMUM_RESEARCH_SOURCE_CALLS
