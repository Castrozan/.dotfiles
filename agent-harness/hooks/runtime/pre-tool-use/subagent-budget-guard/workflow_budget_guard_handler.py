from __future__ import annotations

import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

import subagent_spawn_budget_state  # noqa: E402
import workflow_script_budget_prelude  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)

WORKFLOW_TOOL_NAME = "Workflow"
ORCHESTRATED_WORKFLOW_AGENT_CEILING = 32
ORCHESTRATED_WORKFLOW_OUTPUT_TOKEN_CEILING = 400_000
LIGHT_TIER_WORKFLOW_OUTPUT_TOKEN_CEILING = 100_000
WORKFLOW_SOURCE_KEYS = ("script", "scriptPath", "name")
SAVED_WORKFLOW_DIRECTORY = Path(".claude") / "workflows"


class WorkflowCeilings:
    def __init__(self, agent_ceiling, output_token_ceiling):
        self.agent_ceiling = agent_ceiling
        self.output_token_ceiling = output_token_ceiling


ORCHESTRATED_WORKFLOW_CEILINGS = WorkflowCeilings(
    ORCHESTRATED_WORKFLOW_AGENT_CEILING, ORCHESTRATED_WORKFLOW_OUTPUT_TOKEN_CEILING
)


def _read_workflow_file(workflow_path):
    try:
        return workflow_path.read_text()
    except OSError:
        return None


def _saved_workflow_source(workflow_name, working_directory):
    for workflows_root in (Path(working_directory), Path.home()):
        saved_workflow_source = _read_workflow_file(
            workflows_root / SAVED_WORKFLOW_DIRECTORY / f"{workflow_name}.js"
        )
        if saved_workflow_source is not None:
            return saved_workflow_source
    return None


def resolve_workflow_source(tool_input, working_directory):
    inline_script = tool_input.get("script")
    if inline_script:
        return inline_script
    script_path = tool_input.get("scriptPath")
    if script_path:
        return _read_workflow_file(Path(script_path).expanduser())
    workflow_name = tool_input.get("name")
    if not workflow_name:
        return None
    return _saved_workflow_source(workflow_name, working_directory)


def reserve_workflow_ceilings(hook_input, tool_input):
    if not is_keyboard_driven_interactive_session():
        return ORCHESTRATED_WORKFLOW_CEILINGS
    allowance = subagent_spawn_budget_state.reserve_workflow_agent_allowance(
        hook_input.get("session_id", ""),
        subagent_spawn_budget_state.declares_the_orchestrated_tier(tool_input),
        subagent_spawn_budget_state.SUBAGENT_CEILING_BELOW_THE_ORCHESTRATED_TIER,
    )
    if allowance is None:
        return None
    if allowance.orchestrated_tier_declared:
        return ORCHESTRATED_WORKFLOW_CEILINGS
    return WorkflowCeilings(
        allowance.granted_agent_count, LIGHT_TIER_WORKFLOW_OUTPUT_TOKEN_CEILING
    )


def refuse(message):
    return HandlerResult(decision="deny", reason=message, system_message=message)


def unresolvable_source_message():
    return (
        "BLOCKED: the workflow budget guard could not read this workflow's script, so it cannot "
        "bound it. Pass the script inline through 'script', or through a readable 'scriptPath'."
    )


def bypassing_constructs_message(construct_names):
    return (
        f"BLOCKED: this workflow script uses {', '.join(construct_names)}, which can reach the "
        f"unbounded agent() around the budget guard's ceiling. Call agent(), parallel() and "
        f"pipeline() directly, and run a child workflow's steps inline instead of through workflow()."
    )


def missing_meta_message():
    return (
        "BLOCKED: the workflow script has no 'export const meta = {...}' declaration, so the "
        "budget guard has nowhere to install its ceiling. Begin the script with that declaration."
    )


def tier_ceiling_reached_message():
    return (
        f"BLOCKED: this session has already spent the "
        f"{subagent_spawn_budget_state.SUBAGENT_CEILING_BELOW_THE_ORCHESTRATED_TIER} delegated "
        f"agents every tier below orchestrated holds to, and a workflow's agents count against the "
        f"same ceiling. Do the rest yourself, or re-attempt this Workflow call with its "
        f"'description' starting with 'orchestrated:' followed by the trigger that justifies it, "
        f"which raises the ceiling to {ORCHESTRATED_WORKFLOW_AGENT_CEILING} agents and "
        f"{ORCHESTRATED_WORKFLOW_OUTPUT_TOKEN_CEILING} Opus-equivalent output tokens per run, with Haiku output weighted 0.025 and Sonnet 0.5."
    )


def ceilings_context(ceilings):
    return (
        f"The workflow budget guard bounds this run to {ceilings.agent_ceiling} agent() calls and "
        f"{ceilings.output_token_ceiling} Opus-equivalent output tokens (Haiku output weighted 0.025, Sonnet 0.5); past either, agent() throws and the "
        f"refusal appears in the run log, so report any work it cut short."
    )


def unguardable_script_message(unguarded_script):
    bypassing_constructs = workflow_script_budget_prelude.prelude_bypassing_constructs(
        unguarded_script
    )
    if bypassing_constructs:
        return bypassing_constructs_message(bypassing_constructs)
    if workflow_script_budget_prelude.meta_declaration_end(unguarded_script) is None:
        return missing_meta_message()
    return None


def unguarded_script_or_refusal(hook_input, tool_input):
    workflow_source = resolve_workflow_source(
        tool_input, hook_input.get("cwd") or str(Path.cwd())
    )
    if workflow_source is None:
        return None, unresolvable_source_message()
    unguarded_script = workflow_script_budget_prelude.script_without_budget_prelude(
        workflow_source
    )
    return unguarded_script, unguardable_script_message(unguarded_script)


def guarded_tool_input(tool_input, unguarded_script, ceilings):
    guarded_input = {
        key: value
        for key, value in tool_input.items()
        if key not in WORKFLOW_SOURCE_KEYS
    }
    guarded_input["script"] = workflow_script_budget_prelude.script_with_budget_prelude(
        unguarded_script, ceilings.agent_ceiling, ceilings.output_token_ceiling
    )
    return guarded_input


def workflow_tool_input(hook_input):
    return hook_input.get("tool_input", {}) or {}


def handle(hook_input):
    if hook_input.get("tool_name", "") != WORKFLOW_TOOL_NAME:
        return None
    tool_input = workflow_tool_input(hook_input)
    unguarded_script, refusal_message = unguarded_script_or_refusal(
        hook_input, tool_input
    )
    if refusal_message is not None:
        return refuse(refusal_message)
    ceilings = reserve_workflow_ceilings(hook_input, tool_input)
    if ceilings is None:
        return refuse(tier_ceiling_reached_message())
    return HandlerResult(
        additional_context=ceilings_context(ceilings),
        updated_input=guarded_tool_input(tool_input, unguarded_script, ceilings),
    )
