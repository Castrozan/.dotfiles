#!/usr/bin/env python3

import argparse
import atexit
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
CORE_INSTRUCTIONS_PATH = REPO_ROOT / "agents" / "core.md"
COMPLIANCE_SKILL_PATH = REPO_ROOT / "agents" / "skills" / "review" / "compliance.md"
E2E_WORKSPACE_PARENT = Path.home() / "repo" / ".e2e-tests"
SESSION_PREFIX = "coached-"

TOOL_CALL_PATTERN = re.compile(r"^[●⬤]\s+(\w+)\((.+)\)\s*$")
TOOL_CALL_MULTILINE_PATTERN = re.compile(r"^[●⬤]\s+(\w+)\((.+)$")
COLLAPSED_READ_PATTERN = re.compile(r"^\s*(?:Read|Reading) \d+ file")
COLLAPSED_SEARCH_PATTERN = re.compile(r"^\s*Searched for \d+ pattern")

TOOL_NAME_NORMALIZATION = {
    "Update": "Edit",
    "Bash": "Bash",
    "Read": "Read",
    "Write": "Write",
    "Glob": "Glob",
    "Grep": "Grep",
}

ACTIVE_SESSIONS: list[str] = []
TMUX_SOCKET: str = ""


def cleanup_sessions():
    if not TMUX_SOCKET:
        return
    for session_name in ACTIVE_SESSIONS:
        subprocess.run(
            ["tmux", "-S", TMUX_SOCKET, "kill-session", "-t", session_name],
            capture_output=True,
            timeout=5,
        )


atexit.register(cleanup_sessions)


@dataclass
class CoachedSessionResult:
    scenario_name: str
    initial_nps: int
    coached_nps: int
    improvement: int
    initial_tool_sequence: list[str]
    coached_tool_sequence: list[str]
    coach_findings: str
    duration_seconds: float
    error: str | None = None


def discover_tmux_socket() -> str:
    uid = os.getuid()
    for search_path in [f"/run/user/{uid}/tmux-{uid}", f"/tmp/tmux-{uid}"]:
        try:
            for entry in Path(search_path).iterdir():
                if entry.name == "default" and entry.is_socket():
                    return str(entry)
        except (FileNotFoundError, PermissionError):
            continue
    return ""


def run_tmux(socket: str, arguments: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", "-S", socket] + arguments,
        capture_output=True,
        text=True,
        timeout=10,
    )


def create_session(socket: str, name: str, working_directory: Path) -> str:
    global TMUX_SOCKET
    TMUX_SOCKET = socket
    ACTIVE_SESSIONS.append(name)
    run_tmux(
        socket,
        [
            "new-session",
            "-d",
            "-s",
            name,
            "-n",
            "test",
            "-c",
            str(working_directory),
            "-x",
            "200",
            "-y",
            "50",
        ],
    )
    return f"{name}:test"


def launch_claude(socket: str, target: str, model: str) -> None:
    run_tmux(
        socket,
        [
            "send-keys",
            "-t",
            target,
            f"claude --model {model} --dangerously-skip-permissions",
            "Enter",
        ],
    )


def dismiss_trust_dialog(socket: str, target: str) -> None:
    for _ in range(15):
        result = run_tmux(
            socket,
            [
                "capture-pane",
                "-t",
                target,
                "-p",
                "-S",
                "-20",
            ],
        )
        if "trust this folder" in result.stdout.lower():
            run_tmux(socket, ["send-keys", "-t", target, "Enter"])
            time.sleep(2)
            return
        if "\u276f" in result.stdout and "trust" not in result.stdout.lower():
            return
        time.sleep(1)


def wait_for_prompt(socket: str, target: str, max_attempts: int = 45) -> bool:
    for attempt in range(max_attempts):
        if attempt == 5:
            dismiss_trust_dialog(socket, target)
        result = run_tmux(
            socket,
            [
                "capture-pane",
                "-t",
                target,
                "-p",
                "-S",
                "-15",
            ],
        )
        if "trust" in result.stdout.lower():
            dismiss_trust_dialog(socket, target)
            continue
        if "\u276f" in result.stdout:
            return True
        time.sleep(1)
    return False


def send_prompt(socket: str, target: str, text: str) -> None:
    collapsed = " ".join(text.strip().split())
    run_tmux(socket, ["send-keys", "-t", target, collapsed, "Enter"])


def wait_for_completion(
    socket: str,
    target: str,
    prompt_text: str,
    timeout_seconds: int = 300,
) -> bool:
    prompt_fragment = " ".join(prompt_text.strip().split()[:4])
    elapsed = 0.0
    while elapsed < 15.0:
        time.sleep(1.0)
        elapsed += 1.0
        result = run_tmux(
            socket,
            [
                "capture-pane",
                "-t",
                target,
                "-p",
                "-S",
                "-30",
            ],
        )
        if prompt_fragment in result.stdout:
            break

    time.sleep(15)
    elapsed += 15.0

    consecutive_sightings = 0
    while elapsed < timeout_seconds:
        time.sleep(5.0)
        elapsed += 5.0
        result = run_tmux(
            socket,
            [
                "capture-pane",
                "-t",
                target,
                "-p",
                "-S",
                "-10",
            ],
        )
        lines = result.stdout.strip().split("\n")
        found = any(
            line.strip() == "\u276f" or line.strip().startswith("\u276f ")
            for line in lines
        )
        if found:
            consecutive_sightings += 1
            if consecutive_sightings >= 3:
                return True
        else:
            consecutive_sightings = 0
    return False


def capture_output(socket: str, target: str) -> str:
    result = run_tmux(
        socket,
        [
            "capture-pane",
            "-t",
            target,
            "-p",
            "-S",
            "-99999",
            "-J",
        ],
    )
    return result.stdout


def destroy_session(socket: str, name: str) -> None:
    run_tmux(socket, ["send-keys", "-t", f"{name}:test", "/exit", "Enter"])
    time.sleep(2)
    run_tmux(socket, ["kill-session", "-t", name])
    if name in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.remove(name)


def parse_tool_sequence(raw_output: str) -> list[str]:
    tool_names = []
    for line in raw_output.split("\n"):
        stripped = line.strip()
        match = TOOL_CALL_PATTERN.match(stripped)
        if not match:
            match = TOOL_CALL_MULTILINE_PATTERN.match(stripped)
        if match:
            raw_name = match.group(1)
            tool_names.append(TOOL_NAME_NORMALIZATION.get(raw_name, raw_name))
            continue
        without_bullet = stripped.lstrip("\u25cf\u2b24 ")
        if COLLAPSED_READ_PATTERN.match(without_bullet):
            tool_names.append("Read")
        elif COLLAPSED_SEARCH_PATTERN.match(without_bullet):
            tool_names.append("Grep")
    return tool_names


def calculate_nps_from_tool_sequence_and_workspace(
    tool_sequence: list[str],
    workspace: Path,
    scenario: dict,
) -> int:
    score = 50
    read_count = tool_sequence.count("Read")
    edit_count = tool_sequence.count("Edit") + tool_sequence.count("Write")

    if edit_count > 0:
        if read_count == 0:
            score -= 20
        else:
            first_read = next(
                (i for i, n in enumerate(tool_sequence) if n == "Read"), 999
            )
            first_edit = next(
                (i for i, n in enumerate(tool_sequence) if n in ("Edit", "Write")),
                999,
            )
            if first_read < first_edit:
                score += 10
            else:
                score -= 15
            ratio = read_count / edit_count
            if ratio >= 2.0:
                score += 10
            elif ratio >= 1.0:
                score += 5
    elif len(tool_sequence) > 0:
        score -= 10

    for file_def in scenario.get("setup", {}).get("files", []):
        file_path = workspace / file_def["path"]
        if file_path.exists():
            content = file_path.read_text()
            if any(p in content for p in ("# ", "// ", "/* ")):
                if not (content.startswith("#!") and content.count("# ") == 1):
                    score -= 10
                    break

    setup_files = [f["path"] for f in scenario.get("setup", {}).get("files", [])]
    try:
        initial_sha_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        initial_sha = initial_sha_result.stdout.strip().split("\n")[0]
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", initial_sha, "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        uncommitted_result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        all_changed = set(
            diff_result.stdout.strip().split("\n")
            + uncommitted_result.stdout.strip().split("\n")
        )
        changed_count = sum(1 for f in setup_files if f in all_changed)
        expected_count = len(setup_files)
        if expected_count > 0:
            change_ratio = changed_count / expected_count
            score += int(change_ratio * 15)
    except Exception:
        pass

    return max(0, min(score, 100))


def load_compliance_skill_body() -> str:
    content = COMPLIANCE_SKILL_PATH.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def load_core_instructions_body() -> str:
    content = CORE_INSTRUCTIONS_PATH.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def setup_workspace(scenario: dict, workspace: Path) -> None:
    instructions = load_core_instructions_body()
    (workspace / "CLAUDE.md").write_text(instructions + "\n")

    for file_def in scenario.get("setup", {}).get("files", []):
        relative_path = file_def["path"]
        file_path = workspace / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_def["content"])

    if scenario.get("setup", {}).get("git_init", False):
        git_env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@test",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@test",
        }
        subprocess.run(
            ["git", "init"],
            cwd=workspace,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=workspace,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=workspace,
            capture_output=True,
            check=True,
            timeout=10,
            env=git_env,
        )


def build_coach_prompt(tool_sequence: list[str], workspace: Path) -> str:
    try:
        initial_sha_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        initial_sha = initial_sha_result.stdout.strip().split("\n")[0]
        diff_result = subprocess.run(
            ["git", "diff", initial_sha],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        git_diff = diff_result.stdout[:3000]
    except Exception:
        git_diff = "(could not get diff)"

    tool_list = " -> ".join(tool_sequence) if tool_sequence else "(no tools used)"

    return (
        f"Review this agent's work for compliance violations.\n\n"
        f"Tool sequence: {tool_list}\n\n"
        f"Git diff:\n```\n{git_diff}\n```\n\n"
        f"Check each rule and report PASS/FAIL/UNKNOWN."
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


def print_coached_results(results: list[CoachedSessionResult]) -> None:
    print("\n" + "=" * 70)
    print("COACHED SESSION RESULTS (worker + compliance coach)")
    print("=" * 70 + "\n")

    for result in results:
        improvement_color = (
            "\033[32m"
            if result.improvement > 0
            else "\033[33m"
            if result.improvement == 0
            else "\033[31m"
        )
        reset = "\033[0m"

        initial_color = (
            "\033[32m"
            if result.initial_nps >= 75
            else "\033[33m"
            if result.initial_nps >= 50
            else "\033[31m"
        )
        coached_color = (
            "\033[32m"
            if result.coached_nps >= 75
            else "\033[33m"
            if result.coached_nps >= 50
            else "\033[31m"
        )

        print(f"  {result.scenario_name} ({result.duration_seconds:.0f}s)")
        print(
            f"    Initial: {initial_color}NPS {result.initial_nps}{reset}"
            f"  ->  Coached: {coached_color}NPS {result.coached_nps}{reset}"
            f"  ({improvement_color}{result.improvement:+d}{reset})"
        )

        if result.error:
            print(f"    Error: {result.error}")

        if result.coach_findings:
            for line in result.coach_findings.split("\n"):
                stripped = line.strip()
                if stripped.startswith("FAIL:"):
                    print(f"    \033[31m{stripped}\033[0m")
                elif stripped.startswith("PASS:"):
                    print(f"    \033[32m{stripped}\033[0m")

        print()

    initial_avg = sum(r.initial_nps for r in results) / len(results) if results else 0
    coached_avg = sum(r.coached_nps for r in results) / len(results) if results else 0
    improvement_avg = coached_avg - initial_avg

    print(f"{'=' * 70}")
    print(
        f"  Initial: {initial_avg:.0f}  ->  "
        f"Coached: {coached_avg:.0f}  "
        f"({improvement_avg:+.0f})"
    )
    print(f"{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run coached session tests (worker + compliance coach)",
    )
    parser.add_argument("--scenario", help="Specific scenario name")
    parser.add_argument("--model", default="opus", help="Model for worker")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--scenarios-dir", default=SCENARIOS_DIR, type=Path)
    args = parser.parse_args()

    scenario_files = sorted(args.scenarios_dir.glob("*.yaml"))

    if args.list:
        print("Available scenarios:")
        for sf in scenario_files:
            s = yaml.safe_load(sf.read_text())
            print(f"  {s['name']}: {s.get('description', '')}")
        sys.exit(0)

    if args.scenario:
        scenario_files = [
            sf
            for sf in scenario_files
            if yaml.safe_load(sf.read_text())["name"] == args.scenario
        ]

    results = []
    for sf in scenario_files:
        scenario = yaml.safe_load(sf.read_text())
        print(f"Running coached: {scenario['name']}...")
        result = run_coached_scenario(sf, model=args.model)
        results.append(result)

    print_coached_results(results)


if __name__ == "__main__":
    main()
