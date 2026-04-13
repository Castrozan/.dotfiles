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
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
CORE_INSTRUCTIONS_PATH = REPO_ROOT / "agents" / "core.md"
E2E_WORKSPACE_PARENT = Path.home() / "repo" / ".e2e-tests"
E2E_SESSION_PREFIX = "e2e-test-"

TOOL_CALL_PATTERN = re.compile(r"^[●⬤]\s+(\w+)\((.+)\)\s*$")
TOOL_CALL_MULTILINE_START_PATTERN = re.compile(r"^[●⬤]\s+(\w+)\((.+)$")

TOOL_NAME_NORMALIZATION = {
    "Update": "Edit",
    "Bash": "Bash",
    "Read": "Read",
    "Write": "Write",
    "Glob": "Glob",
    "Grep": "Grep",
    "Skill": "Skill",
    "Agent": "Agent",
    "ToolSearch": "ToolSearch",
}

COLLAPSED_READ_PATTERN = re.compile(r"^\s*(?:Read|Reading) \d+ file")
COLLAPSED_SEARCH_PATTERN = re.compile(r"^\s*Searched for \d+ pattern")
COLLAPSED_LISTED_PATTERN = re.compile(
    r"^\s*(?:Read|Reading) \d+ file|[Ll]isted \d+ director"
)

ACTIVE_TEST_SESSIONS: list[str] = []
ACTIVE_TMUX_SOCKET: str = ""


def cleanup_orphaned_test_sessions():
    if not ACTIVE_TMUX_SOCKET:
        return
    for session_name in ACTIVE_TEST_SESSIONS:
        subprocess.run(
            [
                "tmux",
                "-S",
                ACTIVE_TMUX_SOCKET,
                "kill-session",
                "-t",
                session_name,
            ],
            capture_output=True,
            timeout=5,
        )


atexit.register(cleanup_orphaned_test_sessions)


@dataclass
class TerminalToolCallEvent:
    tool_name: str
    tool_arguments_text: str
    position_in_output: int


@dataclass
class TerminalSessionTrace:
    raw_terminal_output: str = ""
    detected_tool_calls: list[TerminalToolCallEvent] = field(default_factory=list)
    detected_bash_commands: list[str] = field(default_factory=list)
    detected_assistant_text_blocks: list[str] = field(default_factory=list)
    duration_seconds: float = 0
    timed_out: bool = False


@dataclass
class E2eAssertionResult:
    name: str
    passed: bool
    detail: str


@dataclass
class E2eScenarioResult:
    scenario_name: str
    passed: bool
    assertion_results: list[E2eAssertionResult]
    trace: TerminalSessionTrace
    workspace_directory: Path | None
    duration_seconds: float
    experience_score: int = 0
    error: str | None = None


def discover_tmux_socket_path() -> str:
    uid = os.getuid()
    search_paths = [
        f"/run/user/{uid}/tmux-{uid}",
        f"/tmp/tmux-{uid}",
    ]
    for search_path in search_paths:
        try:
            for entry in Path(search_path).iterdir():
                if entry.name == "default" and entry.is_socket():
                    return str(entry)
        except (FileNotFoundError, PermissionError):
            continue
    return ""


def run_tmux_command(
    socket_path: str, tmux_arguments: list[str]
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", "-S", socket_path] + tmux_arguments,
        capture_output=True,
        text=True,
        timeout=10,
    )


def create_isolated_tmux_session_for_test(
    socket_path: str,
    session_name: str,
    working_directory: Path,
) -> str:
    global ACTIVE_TMUX_SOCKET
    ACTIVE_TMUX_SOCKET = socket_path
    ACTIVE_TEST_SESSIONS.append(session_name)

    run_tmux_command(
        socket_path,
        [
            "new-session",
            "-d",
            "-s",
            session_name,
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
    return f"{session_name}:test"


def launch_claude_in_tmux_session(
    socket_path: str,
    tmux_target: str,
    model: str,
) -> None:
    claude_command = f"claude --model {model} --dangerously-skip-permissions"
    run_tmux_command(
        socket_path,
        ["send-keys", "-t", tmux_target, claude_command, "Enter"],
    )


def dismiss_workspace_trust_dialog_if_present(
    socket_path: str,
    tmux_target: str,
) -> None:
    for _ in range(15):
        result = run_tmux_command(
            socket_path,
            [
                "capture-pane",
                "-t",
                tmux_target,
                "-p",
                "-S",
                "-20",
            ],
        )
        captured_text = result.stdout
        if "trust this folder" in captured_text.lower():
            run_tmux_command(
                socket_path,
                [
                    "send-keys",
                    "-t",
                    tmux_target,
                    "Enter",
                ],
            )
            time.sleep(2)
            return
        if "\u276f" in captured_text and "trust" not in captured_text.lower():
            return
        time.sleep(1)


def wait_for_claude_input_prompt_indicator(
    socket_path: str,
    tmux_target: str,
    max_attempts: int = 45,
    interval_seconds: float = 1.0,
) -> bool:
    for attempt in range(max_attempts):
        if attempt == 5:
            dismiss_workspace_trust_dialog_if_present(socket_path, tmux_target)

        result = run_tmux_command(
            socket_path,
            [
                "capture-pane",
                "-t",
                tmux_target,
                "-p",
                "-S",
                "-15",
            ],
        )
        captured_text = result.stdout

        if "trust" in captured_text.lower():
            dismiss_workspace_trust_dialog_if_present(socket_path, tmux_target)
            continue

        if "\u276f" in captured_text:
            return True

        time.sleep(interval_seconds)
    return False


def send_prompt_to_claude_session(
    socket_path: str,
    tmux_target: str,
    prompt_text: str,
) -> None:
    collapsed_prompt = " ".join(prompt_text.strip().split())
    run_tmux_command(
        socket_path,
        [
            "send-keys",
            "-t",
            tmux_target,
            collapsed_prompt,
            "Enter",
        ],
    )


def capture_last_lines(
    socket_path: str,
    tmux_target: str,
    line_count: int = 20,
) -> str:
    result = run_tmux_command(
        socket_path,
        [
            "capture-pane",
            "-t",
            tmux_target,
            "-p",
            "-S",
            f"-{line_count}",
        ],
    )
    return result.stdout


def wait_for_response_completion(
    socket_path: str,
    tmux_target: str,
    prompt_text: str,
    timeout_seconds: int = 300,
    poll_interval_seconds: float = 5.0,
) -> bool:
    prompt_words = prompt_text.strip().split()[:4]
    prompt_fragment = " ".join(prompt_words)

    elapsed = 0.0
    while elapsed < 15.0:
        time.sleep(1.0)
        elapsed += 1.0
        captured = capture_last_lines(socket_path, tmux_target, 30)
        if prompt_fragment in captured:
            break

    time.sleep(15)
    elapsed += 15.0

    consecutive_prompt_sightings = 0
    required_consecutive_sightings = 3

    while elapsed < timeout_seconds:
        time.sleep(poll_interval_seconds)
        elapsed += poll_interval_seconds
        captured = capture_last_lines(socket_path, tmux_target, 10)
        lines = captured.strip().split("\n")
        prompt_found_this_poll = False
        for line in lines:
            stripped = line.strip()
            if stripped == "\u276f" or stripped.startswith("\u276f "):
                prompt_found_this_poll = True
                break

        if prompt_found_this_poll:
            consecutive_prompt_sightings += 1
            if consecutive_prompt_sightings >= required_consecutive_sightings:
                return True
        else:
            consecutive_prompt_sightings = 0
    return False


def capture_full_terminal_output(
    socket_path: str,
    tmux_target: str,
) -> str:
    result = run_tmux_command(
        socket_path,
        [
            "capture-pane",
            "-t",
            tmux_target,
            "-p",
            "-S",
            "-99999",
            "-J",
        ],
    )
    return result.stdout


def destroy_test_session(
    socket_path: str,
    session_name: str,
) -> None:
    run_tmux_command(
        socket_path,
        ["send-keys", "-t", f"{session_name}:test", "C-c", ""],
    )
    time.sleep(1)
    run_tmux_command(
        socket_path,
        ["send-keys", "-t", f"{session_name}:test", "/exit", "Enter"],
    )
    time.sleep(2)
    run_tmux_command(
        socket_path,
        ["kill-session", "-t", session_name],
    )
    if session_name in ACTIVE_TEST_SESSIONS:
        ACTIVE_TEST_SESSIONS.remove(session_name)


def parse_tool_calls_from_terminal_output(
    raw_output: str,
) -> list[TerminalToolCallEvent]:
    tool_calls = []
    lines = raw_output.split("\n")

    for line_index, line in enumerate(lines):
        stripped_line = line.strip()

        single_line_match = TOOL_CALL_PATTERN.match(stripped_line)
        if single_line_match:
            raw_tool_name = single_line_match.group(1)
            tool_arguments = single_line_match.group(2)
            normalized_tool_name = TOOL_NAME_NORMALIZATION.get(
                raw_tool_name, raw_tool_name
            )
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name=normalized_tool_name,
                    tool_arguments_text=tool_arguments,
                    position_in_output=line_index,
                )
            )
            continue

        multiline_match = TOOL_CALL_MULTILINE_START_PATTERN.match(stripped_line)
        if multiline_match:
            raw_tool_name = multiline_match.group(1)
            tool_arguments = multiline_match.group(2)
            normalized_tool_name = TOOL_NAME_NORMALIZATION.get(
                raw_tool_name, raw_tool_name
            )
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name=normalized_tool_name,
                    tool_arguments_text=tool_arguments,
                    position_in_output=line_index,
                )
            )
            continue

        without_bullet = stripped_line.lstrip("\u25cf\u2b24 ")

        if COLLAPSED_READ_PATTERN.match(without_bullet):
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name="Read",
                    tool_arguments_text=without_bullet,
                    position_in_output=line_index,
                )
            )
            continue

        if COLLAPSED_SEARCH_PATTERN.match(without_bullet):
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name="Grep",
                    tool_arguments_text=without_bullet,
                    position_in_output=line_index,
                )
            )

    return tool_calls


def extract_bash_commands_from_tool_calls(
    tool_calls: list[TerminalToolCallEvent],
) -> list[str]:
    return [tc.tool_arguments_text for tc in tool_calls if tc.tool_name == "Bash"]


def extract_assistant_text_from_terminal_output(
    raw_output: str,
) -> list[str]:
    text_blocks = []
    lines = raw_output.split("\n")

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("\u25cf") or stripped.startswith("\u2b24"):
            if not TOOL_CALL_PATTERN.match(
                stripped
            ) and not TOOL_CALL_MULTILINE_START_PATTERN.match(stripped):
                text_content = stripped.lstrip("\u25cf\u2b24 ")
                if text_content:
                    text_blocks.append(text_content)

    return text_blocks


def build_terminal_session_trace(
    raw_output: str,
    duration_seconds: float,
    timed_out: bool,
) -> TerminalSessionTrace:
    tool_calls = parse_tool_calls_from_terminal_output(raw_output)
    bash_commands = extract_bash_commands_from_tool_calls(tool_calls)
    assistant_text = extract_assistant_text_from_terminal_output(raw_output)

    return TerminalSessionTrace(
        raw_terminal_output=raw_output,
        detected_tool_calls=tool_calls,
        detected_bash_commands=bash_commands,
        detected_assistant_text_blocks=assistant_text,
        duration_seconds=duration_seconds,
        timed_out=timed_out,
    )


def extract_tool_name_sequence(
    trace: TerminalSessionTrace,
) -> list[str]:
    return [tc.tool_name for tc in trace.detected_tool_calls]


def extract_invoked_skill_names_from_trace(
    trace: TerminalSessionTrace,
) -> list[str]:
    invoked_skill_names = []
    for tool_call in trace.detected_tool_calls:
        if tool_call.tool_name != "Skill":
            continue
        first_argument_token = tool_call.tool_arguments_text.split(",")[0].strip()
        normalized_skill_name = first_argument_token.strip("\"'").strip()
        if normalized_skill_name:
            invoked_skill_names.append(normalized_skill_name)
    return invoked_skill_names


def check_autonomous_skill_invocation_assertion(
    trace: TerminalSessionTrace,
    expected_skill_name: str,
) -> E2eAssertionResult:
    invoked_skills = extract_invoked_skill_names_from_trace(trace)
    present = expected_skill_name in invoked_skills
    return E2eAssertionResult(
        name=f"autonomously invokes Skill({expected_skill_name})",
        passed=present,
        detail=(
            f"Skill({expected_skill_name}) called (all: {invoked_skills})"
            if present
            else (
                f"Skill({expected_skill_name}) never invoked. "
                f"Skills called: {invoked_skills or 'none'}"
            )
        ),
    )


def check_wrong_skill_not_invoked_assertion(
    trace: TerminalSessionTrace,
    forbidden_skill_name: str,
) -> E2eAssertionResult:
    invoked_skills = extract_invoked_skill_names_from_trace(trace)
    present = forbidden_skill_name in invoked_skills
    return E2eAssertionResult(
        name=f"does NOT invoke wrong Skill({forbidden_skill_name})",
        passed=not present,
        detail=(
            f"wrong skill invoked (all: {invoked_skills})"
            if present
            else f"correctly avoided {forbidden_skill_name}"
        ),
    )


def check_terminal_tool_presence_assertion(
    trace: TerminalSessionTrace,
    required_tool: str,
) -> E2eAssertionResult:
    tool_names = extract_tool_name_sequence(trace)
    present = required_tool in tool_names
    count = tool_names.count(required_tool)
    return E2eAssertionResult(
        name=f"uses {required_tool}",
        passed=present,
        detail=(
            f"{required_tool} called {count} time(s)"
            if present
            else (f"{required_tool} never called. Tools: {tool_names}")
        ),
    )


def check_terminal_tool_ordering_assertion(
    trace: TerminalSessionTrace,
    assertion: dict,
) -> E2eAssertionResult:
    first_tool = assertion["tool"]
    second_tool = assertion["before"]
    tool_names = extract_tool_name_sequence(trace)

    first_index = next(
        (i for i, n in enumerate(tool_names) if n == first_tool),
        None,
    )
    second_index = next(
        (i for i, n in enumerate(tool_names) if n == second_tool),
        None,
    )

    if first_index is None:
        return E2eAssertionResult(
            name=f"{first_tool} before {second_tool}",
            passed=False,
            detail=f"{first_tool} never called",
        )
    if second_index is None:
        return E2eAssertionResult(
            name=f"{first_tool} before {second_tool}",
            passed=False,
            detail=f"{second_tool} never called",
        )

    passed = first_index < second_index
    return E2eAssertionResult(
        name=f"{first_tool} before {second_tool}",
        passed=passed,
        detail=(
            f"order correct ({first_index} < {second_index})"
            if passed
            else f"wrong order ({first_index} >= {second_index})"
        ),
    )


def check_bash_command_contains_assertion(
    trace: TerminalSessionTrace,
    expected_substring: str,
) -> E2eAssertionResult:
    found = any(expected_substring in cmd for cmd in trace.detected_bash_commands)
    found_in_raw = expected_substring in trace.raw_terminal_output
    passed = found or found_in_raw
    return E2eAssertionResult(
        name=f"bash ran '{expected_substring}'",
        passed=passed,
        detail=(
            "found in commands"
            if found
            else ("found in raw output" if found_in_raw else "not found")
        ),
    )


def check_bash_command_not_contains_assertion(
    trace: TerminalSessionTrace,
    forbidden_substring: str,
) -> E2eAssertionResult:
    found_in_commands = any(
        forbidden_substring in cmd for cmd in trace.detected_bash_commands
    )
    found_in_raw = forbidden_substring in trace.raw_terminal_output
    absent = not found_in_commands and not found_in_raw
    return E2eAssertionResult(
        name=f"did not run '{forbidden_substring}'",
        passed=absent,
        detail=("correctly absent" if absent else "found in session"),
    )


def check_workspace_file_no_comments_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return E2eAssertionResult(
            name=f"{file_path} has no comments",
            passed=False,
            detail="file does not exist",
        )
    content = full_path.read_text()
    comment_patterns = ["# ", "// ", "/* ", "# TODO", "# FIXME"]
    found_comments = [p for p in comment_patterns if p in content]
    if not found_comments:
        return E2eAssertionResult(
            name=f"{file_path} has no comments",
            passed=True,
            detail="no comments found",
        )

    shebang_only = (
        found_comments == ["# "]
        and content.startswith("#!")
        and content.count("# ") == 1
    )
    if shebang_only:
        return E2eAssertionResult(
            name=f"{file_path} has no comments",
            passed=True,
            detail="only shebang line",
        )

    return E2eAssertionResult(
        name=f"{file_path} has no comments",
        passed=False,
        detail=f"found: {found_comments}",
    )


def check_workspace_file_changed_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    try:
        initial_commit_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        initial_sha = initial_commit_result.stdout.strip().split("\n")[0]

        diff_result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                initial_sha,
                "HEAD",
            ],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        committed_changes = diff_result.stdout.strip().split("\n")

        uncommitted_result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        uncommitted = uncommitted_result.stdout.strip().split("\n")

        all_changed = set(committed_changes + uncommitted)
        was_changed = file_path in all_changed
        return E2eAssertionResult(
            name=f"{file_path} was modified",
            passed=was_changed,
            detail=(
                "file was modified"
                if was_changed
                else f"unchanged. Changed: {list(all_changed)}"
            ),
        )
    except Exception:
        return E2eAssertionResult(
            name=f"{file_path} was modified",
            passed=False,
            detail="could not check git status",
        )


def check_workspace_formatted_correctly_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return E2eAssertionResult(
            name=f"{file_path} is formatted",
            passed=False,
            detail="file does not exist",
        )

    if file_path.endswith(".py"):
        result = subprocess.run(
            ["ruff", "check", "--select=E,F,W", str(full_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        passed = result.returncode == 0
        return E2eAssertionResult(
            name=f"{file_path} is formatted",
            passed=passed,
            detail=(
                "ruff check passed" if passed else f"ruff errors: {result.stdout[:200]}"
            ),
        )

    return E2eAssertionResult(
        name=f"{file_path} is formatted",
        passed=True,
        detail="no formatter check available",
    )


def run_e2e_assertions(
    trace: TerminalSessionTrace,
    assertions: dict,
    workspace_directory: Path | None = None,
) -> list[E2eAssertionResult]:
    results = []

    for ordering in assertions.get("tool_order", []):
        results.append(check_terminal_tool_ordering_assertion(trace, ordering))

    for required_tool in assertions.get("tool_presence", []):
        results.append(check_terminal_tool_presence_assertion(trace, required_tool))

    for expected_skill_name in assertions.get("autonomous_skill_invocation", []):
        results.append(
            check_autonomous_skill_invocation_assertion(trace, expected_skill_name)
        )

    for forbidden_skill_name in assertions.get("wrong_skill_not_invoked", []):
        results.append(
            check_wrong_skill_not_invoked_assertion(trace, forbidden_skill_name)
        )

    for expected in assertions.get("bash_command_contains", []):
        results.append(check_bash_command_contains_assertion(trace, expected))

    for forbidden in assertions.get("bash_command_not_contains", []):
        results.append(check_bash_command_not_contains_assertion(trace, forbidden))

    if workspace_directory:
        for file_path in assertions.get("workspace_file_no_comments", []):
            results.append(
                check_workspace_file_no_comments_assertion(
                    workspace_directory, file_path
                )
            )

        for file_path in assertions.get("file_changed", []):
            results.append(
                check_workspace_file_changed_assertion(workspace_directory, file_path)
            )

        for file_path in assertions.get("workspace_formatted", []):
            results.append(
                check_workspace_formatted_correctly_assertion(
                    workspace_directory, file_path
                )
            )

    return results


def calculate_e2e_experience_score(
    trace: TerminalSessionTrace,
    assertion_results: list[E2eAssertionResult],
    workspace_directory: Path | None = None,
) -> int:
    score = 65
    tool_names = extract_tool_name_sequence(trace)
    edit_count = tool_names.count("Edit") + tool_names.count("Write")

    for command in trace.detected_bash_commands:
        if "git add -A" in command or "git add ." in command:
            score -= 10
            break

    bash_misuse_commands = ["cat ", "head ", "tail ", "find ."]
    for command in trace.detected_bash_commands:
        for bad_pattern in bash_misuse_commands:
            if bad_pattern in command:
                score -= 5
                break

    formatter_ran = any(
        pattern in trace.raw_terminal_output
        for pattern in ("ruff", "nixfmt", "shfmt", "shellcheck")
    )
    if edit_count > 0 and formatter_ran:
        score += 5

    combined_text = " ".join(trace.detected_assistant_text_blocks)
    if "\u2014" in combined_text:
        score -= 5

    if assertion_results:
        passed = sum(1 for a in assertion_results if a.passed)
        failed = len(assertion_results) - passed
        score += passed * 3
        score -= failed * 8

    return max(0, min(score, 100))


def load_core_instructions_with_frontmatter() -> str:
    return CORE_INSTRUCTIONS_PATH.read_text()


def place_claude_md_in_workspace(
    workspace_directory: Path,
    claude_ab_mode: str = "inline",
) -> None:
    instructions_with_frontmatter = load_core_instructions_with_frontmatter()
    instructions_body_only = instructions_with_frontmatter
    parts = instructions_with_frontmatter.split("---", 2)
    if len(parts) >= 3:
        instructions_body_only = parts[2].strip()

    if claude_ab_mode == "reference":
        (workspace_directory / "AGENTS.md").write_text(instructions_with_frontmatter)
        (workspace_directory / "CLAUDE.md").write_text("@AGENTS.md\n")
    elif claude_ab_mode == "inline":
        (workspace_directory / "CLAUDE.md").write_text(instructions_body_only + "\n")
    elif claude_ab_mode == "global-only":
        pass


def setup_e2e_scenario_workspace(
    scenario: dict,
    workspace_directory: Path,
    claude_ab_mode: str = "inline",
) -> None:
    setup = scenario.get("setup", {})

    project_claude_md_content = setup.get("project_claude_md")
    if project_claude_md_content:
        (workspace_directory / "CLAUDE.md").write_text(project_claude_md_content)
    else:
        place_claude_md_in_workspace(workspace_directory, claude_ab_mode)

    for file_def in setup.get("files", []):
        relative_path = file_def["path"]
        if os.path.isabs(relative_path) or ".." in relative_path:
            raise ValueError(f"path must be relative: {relative_path}")
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_def["content"])

    if setup.get("git_init", False):
        git_env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@test",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@test",
        }
        subprocess.run(
            ["git", "init"],
            cwd=workspace_directory,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=workspace_directory,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=workspace_directory,
            capture_output=True,
            check=True,
            timeout=10,
            env=git_env,
        )


def load_scenario(scenario_path: Path) -> dict:
    with open(scenario_path) as f:
        return yaml.safe_load(f)


def sanitize_name_for_session(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in name)[:40]


def run_e2e_scenario(
    scenario_path: Path,
    model: str = "haiku",
    dry_run: bool = False,
    debug_capture: bool = False,
    claude_ab_mode: str = "inline",
) -> E2eScenarioResult:
    scenario = load_scenario(scenario_path)
    scenario_name = scenario["name"]

    if dry_run:
        return E2eScenarioResult(
            scenario_name=scenario_name,
            passed=True,
            assertion_results=[],
            trace=TerminalSessionTrace(),
            workspace_directory=None,
            duration_seconds=0,
        )

    socket_path = discover_tmux_socket_path()
    if not socket_path:
        return E2eScenarioResult(
            scenario_name=scenario_name,
            passed=False,
            assertion_results=[],
            trace=TerminalSessionTrace(),
            workspace_directory=None,
            duration_seconds=0,
            error="tmux socket not found",
        )

    sanitized = sanitize_name_for_session(scenario_name)
    timestamp = int(time.time())
    session_name = f"{E2E_SESSION_PREFIX}{sanitized}-{timestamp}"
    E2E_WORKSPACE_PARENT.mkdir(parents=True, exist_ok=True)
    workspace = Path(
        tempfile.mkdtemp(
            prefix=f"e2e-{sanitized}-",
            dir=E2E_WORKSPACE_PARENT,
        )
    )
    timeout = scenario.get("timeout", 300)

    try:
        setup_e2e_scenario_workspace(scenario, workspace, claude_ab_mode)

        tmux_target = create_isolated_tmux_session_for_test(
            socket_path, session_name, workspace
        )

        launch_claude_in_tmux_session(socket_path, tmux_target, model)

        if not wait_for_claude_input_prompt_indicator(
            socket_path, tmux_target, max_attempts=45
        ):
            return E2eScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=TerminalSessionTrace(),
                workspace_directory=workspace,
                duration_seconds=0,
                error="Claude failed to start (no prompt detected)",
            )

        prompts = scenario.get("prompts", [])
        if not prompts:
            single_prompt = scenario.get("prompt", "")
            if single_prompt:
                prompts = [single_prompt]

        start_time = time.time()

        for prompt_text in prompts:
            send_prompt_to_claude_session(socket_path, tmux_target, prompt_text)
            completed = wait_for_response_completion(
                socket_path,
                tmux_target,
                prompt_text=prompt_text,
                timeout_seconds=timeout,
            )
            if not completed:
                raw_output = capture_full_terminal_output(socket_path, tmux_target)
                duration = time.time() - start_time
                trace = build_terminal_session_trace(
                    raw_output, duration, timed_out=True
                )

                if debug_capture:
                    save_debug_capture(scenario_name, raw_output)

                assertion_results = run_e2e_assertions(
                    trace,
                    scenario.get("assertions", {}),
                    workspace,
                )
                experience_score = calculate_e2e_experience_score(
                    trace, assertion_results, workspace
                )

                return E2eScenarioResult(
                    scenario_name=scenario_name,
                    passed=False,
                    assertion_results=assertion_results,
                    trace=trace,
                    workspace_directory=workspace,
                    duration_seconds=duration,
                    experience_score=experience_score,
                    error=f"Timed out after {timeout}s",
                )

        raw_output = capture_full_terminal_output(socket_path, tmux_target)
        duration = time.time() - start_time

        if debug_capture:
            save_debug_capture(scenario_name, raw_output)

        trace = build_terminal_session_trace(raw_output, duration, timed_out=False)

        assertion_results = run_e2e_assertions(
            trace,
            scenario.get("assertions", {}),
            workspace,
        )
        all_passed = all(a.passed for a in assertion_results)
        experience_score = calculate_e2e_experience_score(
            trace, assertion_results, workspace
        )

        return E2eScenarioResult(
            scenario_name=scenario_name,
            passed=all_passed,
            assertion_results=assertion_results,
            trace=trace,
            workspace_directory=workspace,
            duration_seconds=duration,
            experience_score=experience_score,
        )

    finally:
        destroy_test_session(socket_path, session_name)
        shutil.rmtree(workspace, ignore_errors=True)


def save_debug_capture(scenario_name: str, raw_output: str) -> None:
    debug_directory = Path("/tmp/e2e-debug-captures")
    debug_directory.mkdir(exist_ok=True)
    timestamp = int(time.time())
    output_file = debug_directory / f"{scenario_name}-{timestamp}.txt"
    output_file.write_text(raw_output)
    print(f"    Debug capture saved: {output_file}")


def print_e2e_results(
    results: list[E2eScenarioResult],
) -> bool:
    print("\n" + "=" * 60)
    print("E2E INTEGRATION TEST RESULTS (tmux sessions)")
    print("=" * 60 + "\n")

    all_passed = True

    for result in results:
        status = "\u2713" if result.passed else "\u2717"
        color = "\033[32m" if result.passed else "\033[31m"
        score_color = (
            "\033[32m"
            if result.experience_score >= 75
            else "\033[33m"
            if result.experience_score >= 50
            else "\033[31m"
        )
        reset = "\033[0m"

        print(
            f"{color}{status}{reset} "
            f"{result.scenario_name} "
            f"({result.duration_seconds:.1f}s) "
            f"{score_color}NPS:{result.experience_score}"
            f"{reset}"
        )

        if result.error:
            print(f"    Error: {result.error}")

        for a in result.assertion_results:
            a_sym = "\u2713" if a.passed else "\u2717"
            a_col = "\033[32m" if a.passed else "\033[31m"
            print(f"    {a_col}{a_sym}{reset} {a.name}: {a.detail}")

        if not result.passed:
            all_passed = False
            tool_seq = extract_tool_name_sequence(result.trace)
            if tool_seq:
                print(f"    Tools: {' -> '.join(tool_seq)}")

    scored = [r for r in results if r.experience_score > 0]
    avg_score = sum(r.experience_score for r in scored) / len(scored) if scored else 0
    passed_count = sum(1 for r in results if r.passed)
    total_time = sum(r.duration_seconds for r in results)

    print(f"\n{'=' * 60}")
    print(f"Passed: {passed_count}/{len(results)}")
    print(f"Experience Score: {avg_score:.0f}/100")
    print(f"Total time: {total_time:.1f}s")
    print(f"{'=' * 60}\n")

    return all_passed


def discover_scenario_files(
    scenarios_dir: Path,
) -> list[Path]:
    return sorted(scenarios_dir.rglob("*.yaml"))


def print_multi_run_pass_rate_summary(
    results: list[E2eScenarioResult],
    runs_per_scenario: int,
) -> None:
    grouped_results_by_scenario: dict[str, list[E2eScenarioResult]] = {}
    for result in results:
        grouped_results_by_scenario.setdefault(result.scenario_name, []).append(result)

    print(f"\n{'=' * 60}")
    print(f"MULTI-RUN PASS-RATE SUMMARY ({runs_per_scenario} runs per scenario)")
    print(f"{'=' * 60}\n")

    for scenario_name, scenario_runs in grouped_results_by_scenario.items():
        passed_runs = sum(1 for r in scenario_runs if r.passed)
        total_runs = len(scenario_runs)
        scored_runs = [r for r in scenario_runs if r.experience_score > 0]
        avg_nps = (
            sum(r.experience_score for r in scored_runs) / len(scored_runs)
            if scored_runs
            else 0
        )
        print(f"  {scenario_name}: {passed_runs}/{total_runs} (NPS avg {avg_nps:.0f})")

    total_runs = len(results)
    total_passed = sum(1 for r in results if r.passed)
    print(f"\n  overall: {total_passed}/{total_runs}")
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description=("E2E tmux-based Claude Code integration tests")
    )
    parser.add_argument("--scenario", help="Run specific scenario by name")
    parser.add_argument("--model", default="sonnet", help="Model (default: sonnet)")
    parser.add_argument("--dry-run", action="store_true", help="List without running")
    parser.add_argument("--list", action="store_true", help="List scenarios")
    parser.add_argument(
        "--debug-capture",
        action="store_true",
        help="Save raw terminal output for parser calibration",
    )
    parser.add_argument(
        "--claude-ab-mode",
        default="inline",
        choices=["reference", "inline", "global-only"],
        help="Instructions loading: inline, reference, or global-only",
    )
    parser.add_argument(
        "--scenarios-dir",
        default=SCENARIOS_DIR,
        type=Path,
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Run scenarios in parallel (each in its own tmux session)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help=(
            "Execute each scenario N independent times for stochasticity stats. "
            "Each run is an independent tmux session; parallel cap is --workers "
            "(total concurrent tmux sessions = min(workers, scenarios * runs))."
        ),
    )
    args = parser.parse_args()

    if args.runs < 1:
        print("Error: --runs must be >= 1")
        sys.exit(1)

    scenario_files = discover_scenario_files(args.scenarios_dir)

    if not scenario_files:
        print("No scenarios found in", args.scenarios_dir)
        sys.exit(1)

    if args.list:
        print("Available E2E scenarios:")
        for sf in scenario_files:
            s = load_scenario(sf)
            print(f"  {s['name']}: {s.get('description', '')}")
        sys.exit(0)

    if args.scenario:
        scenario_files = [
            sf for sf in scenario_files if load_scenario(sf)["name"] == args.scenario
        ]
        if not scenario_files:
            print(f"Scenario '{args.scenario}' not found")
            sys.exit(1)

    if not args.dry_run:
        for tool in ["claude", "tmux"]:
            if subprocess.run(["which", tool], capture_output=True).returncode != 0:
                print(f"Error: {tool} not found")
                sys.exit(1)

    def run_one_scenario_file(scenario_file):
        scenario = load_scenario(scenario_file)
        print(f"Running: {scenario['name']}...", flush=True)
        return run_e2e_scenario(
            scenario_file,
            model=args.model,
            dry_run=args.dry_run,
            debug_capture=args.debug_capture,
            claude_ab_mode=args.claude_ab_mode,
        )

    execution_units = list(scenario_files) * args.runs

    results = []
    if args.workers <= 1:
        for sf in execution_units:
            results.append(run_one_scenario_file(sf))
    else:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            for result in executor.map(run_one_scenario_file, execution_units):
                results.append(result)

    all_passed = print_e2e_results(results)

    if args.runs > 1:
        print_multi_run_pass_rate_summary(results, args.runs)
        total_runs = len(results)
        total_passed = sum(1 for r in results if r.passed)
        sys.exit(0 if total_passed == total_runs else 1)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
