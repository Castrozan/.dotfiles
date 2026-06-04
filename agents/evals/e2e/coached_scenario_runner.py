import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import yaml

from coached_fixtures import (
    E2E_WORKSPACE_PARENT,
    build_coach_prompt,
    load_compliance_skill_body,
    setup_workspace,
)
from coached_models import CoachedSessionResult
from coached_scoring import (
    calculate_nps_from_tool_sequence_and_workspace,
    parse_tool_sequence,
)
from coached_tmux import (
    SESSION_PREFIX,
    create_session,
    destroy_session,
    discover_tmux_socket,
    launch_claude,
)
from coached_tmux_io import (
    capture_output,
    send_prompt,
    wait_for_completion,
    wait_for_prompt,
)


def run_coached_scenario(
    scenario_path: Path,
    model: str = "opus",
) -> CoachedSessionResult:
    scenario = yaml.safe_load(scenario_path.read_text())
    scenario_name = scenario["name"]

    socket = discover_tmux_socket()
    if not socket:
        return CoachedSessionResult(
            scenario_name=scenario_name,
            initial_nps=0,
            coached_nps=0,
            improvement=0,
            initial_tool_sequence=[],
            coached_tool_sequence=[],
            coach_findings="",
            duration_seconds=0,
            error="tmux socket not found",
        )

    E2E_WORKSPACE_PARENT.mkdir(parents=True, exist_ok=True)
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", scenario_name)[:30]
    timestamp = int(time.time())
    workspace = Path(
        tempfile.mkdtemp(
            prefix=f"coached-{sanitized}-",
            dir=E2E_WORKSPACE_PARENT,
        )
    )
    worker_session = f"{SESSION_PREFIX}worker-{timestamp}"
    timeout = scenario.get("timeout", 300)

    try:
        setup_workspace(scenario, workspace)
        start_time = time.time()

        worker_target = create_session(socket, worker_session, workspace)
        launch_claude(socket, worker_target, model)

        if not wait_for_prompt(socket, worker_target):
            return CoachedSessionResult(
                scenario_name=scenario_name,
                initial_nps=0,
                coached_nps=0,
                improvement=0,
                initial_tool_sequence=[],
                coached_tool_sequence=[],
                coach_findings="",
                duration_seconds=time.time() - start_time,
                error="Worker failed to start",
            )

        prompt_text = scenario.get("prompt", "")
        send_prompt(socket, worker_target, prompt_text)
        wait_for_completion(socket, worker_target, prompt_text, timeout)

        initial_output = capture_output(socket, worker_target)
        initial_tools = parse_tool_sequence(initial_output)
        initial_nps = calculate_nps_from_tool_sequence_and_workspace(
            initial_tools,
            workspace,
            scenario,
        )

        compliance_body = load_compliance_skill_body()
        coach_prompt = build_coach_prompt(initial_tools, workspace)
        coach_result = subprocess.run(
            [
                "claude",
                "-p",
                "--model",
                "haiku",
                "--system-prompt",
                compliance_body,
                coach_prompt,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=workspace,
        )
        coach_findings = coach_result.stdout.strip()

        initial_fail_count = coach_findings.count("FAIL:")
        initial_nps = max(0, initial_nps - (initial_fail_count * 15))

        has_failures = initial_fail_count > 0

        if has_failures:
            correction_prompt = (
                "The compliance reviewer found these "
                "violations in your work:\n\n"
                f"{coach_findings}\n\n"
                "Fix each FAIL finding now."
            )
            send_prompt(socket, worker_target, correction_prompt)
            wait_for_completion(
                socket,
                worker_target,
                correction_prompt,
                timeout,
            )

        coached_output = capture_output(socket, worker_target)
        coached_tools = parse_tool_sequence(coached_output)
        coached_workspace_nps = calculate_nps_from_tool_sequence_and_workspace(
            coached_tools,
            workspace,
            scenario,
        )

        if has_failures:
            coached_coach_prompt = build_coach_prompt(coached_tools, workspace)
            coached_coach_result = subprocess.run(
                [
                    "claude",
                    "-p",
                    "--model",
                    "haiku",
                    "--system-prompt",
                    compliance_body,
                    coached_coach_prompt,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=workspace,
            )
            coached_findings = coached_coach_result.stdout.strip()
            coached_fail_count = coached_findings.count("FAIL:")
            coached_nps = max(
                0,
                coached_workspace_nps - (coached_fail_count * 15),
            )
            coach_findings += "\n\n--- AFTER CORRECTION ---\n" + coached_findings
        else:
            coached_nps = coached_workspace_nps

        duration = time.time() - start_time

        return CoachedSessionResult(
            scenario_name=scenario_name,
            initial_nps=initial_nps,
            coached_nps=coached_nps,
            improvement=coached_nps - initial_nps,
            initial_tool_sequence=initial_tools,
            coached_tool_sequence=coached_tools,
            coach_findings=coach_findings,
            duration_seconds=duration,
        )

    finally:
        destroy_session(socket, worker_session)
        shutil.rmtree(workspace, ignore_errors=True)
