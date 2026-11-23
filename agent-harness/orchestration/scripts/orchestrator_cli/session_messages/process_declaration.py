from __future__ import annotations

import re

WORKFLOW_PROCESS = "Workflow"
PROCESS_DECLARATION = re.compile(r"^(?P<kind>Workflow|Design|None):\s*(?P<value>\S.*)$")
PROCESS_ADVICE = (
    "the Process section must hold one line, `Workflow: <command>`, `Design: <where "
    "the designed process lives>` or `None: <why no workflow fits>`, since repeatable, "
    "checkable work runs as a workflow and a free session is for discovery"
)


def installed_workflows_advice(workflow_purposes: dict[str, str]) -> str:
    if not workflow_purposes:
        return "no workflow command is installed on this machine"
    return "installed workflows: " + "; ".join(
        f"`{command}` ({purpose})" for command, purpose in workflow_purposes.items()
    )


def process_problems(
    process_lines: list[str], workflow_purposes: dict[str, str]
) -> list[str]:
    installed = installed_workflows_advice(workflow_purposes)
    declaration = (
        PROCESS_DECLARATION.match(process_lines[0]) if len(process_lines) == 1 else None
    )
    if declaration is None:
        return [f"{PROCESS_ADVICE}; {installed}"]
    if declaration["kind"] != WORKFLOW_PROCESS:
        return []
    command = declaration["value"].split()[0].strip("`")
    if command in workflow_purposes:
        return []
    return [
        f"the Process section names `{command}`, which is not an installed workflow; {installed}"
    ]
