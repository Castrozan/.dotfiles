#!/usr/bin/env python3

import argparse
import json
import os
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


@dataclass
class ToolCallEvent:
    tool_name: str
    tool_input: dict
    timestamp: float


@dataclass
class SessionTrace:
    tool_calls: list[ToolCallEvent] = field(default_factory=list)
    assistant_messages: list[str] = field(default_factory=list)
    full_output: str = ""
    duration_seconds: float = 0
    exit_code: int = 0


@dataclass
class AssertionResult:
    name: str
    passed: bool
    detail: str


@dataclass
class ScenarioResult:
    scenario_name: str
    passed: bool
    assertion_results: list[AssertionResult]
    trace: SessionTrace
    workspace_directory: Path | None
    duration_seconds: float
    error: str | None = None


def load_core_system_prompt() -> str | None:
    if not CORE_INSTRUCTIONS_PATH.exists():
        return None
    content = CORE_INSTRUCTIONS_PATH.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def load_scenario(scenario_path: Path) -> dict:
    with open(scenario_path) as scenario_file:
        return yaml.safe_load(scenario_file)


def validate_file_path_is_relative(file_path: str) -> bool:
    return not os.path.isabs(file_path) and ".." not in file_path


def setup_scenario_workspace(scenario: dict, workspace_directory: Path) -> None:
    setup = scenario.get("setup", {})

    for file_definition in setup.get("files", []):
        relative_path = file_definition["path"]
        if not validate_file_path_is_relative(relative_path):
            raise ValueError(
                f"Scenario file path must be relative without ..: {relative_path}"
            )
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_definition["content"])

    if setup.get("git_init", False):
        git_environment = {
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
            timeout=10,
            check=True,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=workspace_directory,
            capture_output=True,
            timeout=10,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=workspace_directory,
            capture_output=True,
            timeout=10,
            check=True,
            env=git_environment,
        )


def run_claude_session(
    prompt: str,
    workspace_directory: Path,
    system_prompt: str | None = None,
    timeout_seconds: int = 180,
    model: str = "sonnet",
) -> SessionTrace:
    command = [
        "claude",
        "-p",
        "--verbose",
        "--output-format",
        "stream-json",
        "--model",
        model,
    ]

    if system_prompt:
        command.extend(["--system-prompt", system_prompt])

    command.append(prompt)

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=timeout_seconds,
            env={
                key: value for key, value in os.environ.items() if key != "CLAUDECODE"
            },
        )
    except subprocess.TimeoutExpired:
        return SessionTrace(
            full_output=(f"Session timed out after {timeout_seconds}s"),
            duration_seconds=time.time() - start_time,
            exit_code=124,
        )

    duration = time.time() - start_time
    trace = parse_stream_json_output(result.stdout)
    trace.full_output = result.stdout + result.stderr
    trace.duration_seconds = duration
    trace.exit_code = result.returncode
    return trace


def extract_tool_calls_from_assistant_message(
    message_data: dict,
) -> list[ToolCallEvent]:
    extracted_tool_calls = []
    message = message_data.get("message", message_data)
    content_blocks = message.get("content", [])

    if not isinstance(content_blocks, list):
        return extracted_tool_calls

    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_use":
            extracted_tool_calls.append(
                ToolCallEvent(
                    tool_name=block.get("name", ""),
                    tool_input=block.get("input", {}),
                    timestamp=time.time(),
                )
            )

    return extracted_tool_calls


def extract_text_from_assistant_message(
    message_data: dict,
) -> str | None:
    message = message_data.get("message", message_data)
    content_blocks = message.get("content", [])

    if not isinstance(content_blocks, list):
        return None

    text_parts = []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text_content = block.get("text", "")
            if text_content.strip():
                text_parts.append(text_content)

    return " ".join(text_parts) if text_parts else None


def parse_stream_json_output(raw_output: str) -> SessionTrace:
    trace = SessionTrace()

    for line in raw_output.strip().split("\n"):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")

        if event_type == "assistant":
            tool_calls = extract_tool_calls_from_assistant_message(event)
            trace.tool_calls.extend(tool_calls)

            text_content = extract_text_from_assistant_message(event)
            if text_content:
                trace.assistant_messages.append(text_content)

        if event_type == "result":
            result_text = event.get("result", "")
            if isinstance(result_text, str) and result_text.strip():
                trace.assistant_messages.append(result_text)

    return trace


def extract_tool_name_sequence(
    trace: SessionTrace,
) -> list[str]:
    return [tool_call.tool_name for tool_call in trace.tool_calls]


def collect_written_file_content_from_tool_calls(
    trace: SessionTrace,
) -> str:
    written_content_parts = []
    for tool_call in trace.tool_calls:
        if tool_call.tool_name in ("Edit", "Write"):
            new_string = tool_call.tool_input.get("new_string", "")
            content = tool_call.tool_input.get("content", "")
            if new_string:
                written_content_parts.append(new_string)
            if content:
                written_content_parts.append(content)
    return "\n".join(written_content_parts)


def check_tool_ordering_assertion(
    trace: SessionTrace,
    assertion: dict,
) -> AssertionResult:
    tool_that_must_come_first = assertion["tool"]
    tool_that_must_come_after = assertion["before"]
    tool_sequence = extract_tool_name_sequence(trace)

    first_index = next(
        (
            index
            for index, name in enumerate(tool_sequence)
            if name == tool_that_must_come_first
        ),
        None,
    )
    second_index = next(
        (
            index
            for index, name in enumerate(tool_sequence)
            if name == tool_that_must_come_after
        ),
        None,
    )

    if first_index is None:
        return AssertionResult(
            name=(f"{tool_that_must_come_first} before {tool_that_must_come_after}"),
            passed=False,
            detail=f"{tool_that_must_come_first} never called",
        )
    if second_index is None:
        return AssertionResult(
            name=(f"{tool_that_must_come_first} before {tool_that_must_come_after}"),
            passed=False,
            detail=f"{tool_that_must_come_after} never called",
        )

    passed = first_index < second_index
    return AssertionResult(
        name=(f"{tool_that_must_come_first} before {tool_that_must_come_after}"),
        passed=passed,
        detail=(
            f"order correct ({first_index} < {second_index})"
            if passed
            else (f"order wrong ({first_index} >= {second_index})")
        ),
    )


def check_tool_presence_assertion(
    trace: SessionTrace,
    required_tool: str,
) -> AssertionResult:
    tool_sequence = extract_tool_name_sequence(trace)
    present = required_tool in tool_sequence
    call_count = tool_sequence.count(required_tool)
    return AssertionResult(
        name=f"uses {required_tool}",
        passed=present,
        detail=(
            f"{required_tool} called {call_count} time(s)"
            if present
            else (f"{required_tool} never called. Tools used: {tool_sequence}")
        ),
    )


def check_tool_absence_assertion(
    trace: SessionTrace,
    forbidden_tool: str,
) -> AssertionResult:
    tool_sequence = extract_tool_name_sequence(trace)
    absent = forbidden_tool not in tool_sequence
    call_count = tool_sequence.count(forbidden_tool)
    return AssertionResult(
        name=f"does not use {forbidden_tool}",
        passed=absent,
        detail=(
            f"{forbidden_tool} correctly absent"
            if absent
            else (f"{forbidden_tool} called {call_count} time(s)")
        ),
    )


def check_output_contains_assertion(
    trace: SessionTrace,
    expected_substring: str,
) -> AssertionResult:
    combined_output = " ".join(trace.assistant_messages).lower()
    found = expected_substring.lower() in combined_output
    return AssertionResult(
        name=f"output contains '{expected_substring}'",
        passed=found,
        detail=("found" if found else "not found in assistant output"),
    )


def check_output_not_contains_assertion(
    trace: SessionTrace,
    forbidden_substring: str,
) -> AssertionResult:
    combined_output = " ".join(trace.assistant_messages).lower()
    absent = forbidden_substring.lower() not in combined_output
    return AssertionResult(
        name=(f"output does not contain '{forbidden_substring}'"),
        passed=absent,
        detail=("correctly absent" if absent else "found in assistant output"),
    )


def check_written_code_not_contains_assertion(
    trace: SessionTrace,
    forbidden_pattern: str,
) -> AssertionResult:
    written_content = collect_written_file_content_from_tool_calls(trace)
    if not written_content:
        return AssertionResult(
            name=(f"written code does not contain '{forbidden_pattern}'"),
            passed=True,
            detail="no code written via Edit/Write",
        )
    absent = forbidden_pattern not in written_content
    return AssertionResult(
        name=(f"written code does not contain '{forbidden_pattern}'"),
        passed=absent,
        detail=(
            "correctly absent from written code"
            if absent
            else "found in code written via Edit/Write"
        ),
    )


def check_workspace_file_not_contains_assertion(
    workspace_directory: Path,
    file_path: str,
    forbidden_pattern: str,
) -> AssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return AssertionResult(
            name=(f"{file_path} does not contain '{forbidden_pattern}'"),
            passed=False,
            detail=f"file {file_path} does not exist",
        )
    content = full_path.read_text()
    absent = forbidden_pattern not in content
    return AssertionResult(
        name=(f"{file_path} does not contain '{forbidden_pattern}'"),
        passed=absent,
        detail=("correctly absent from file" if absent else "found in file content"),
    )


def check_workspace_file_changed_assertion(
    workspace_directory: Path,
    file_path: str,
) -> AssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return AssertionResult(
            name=f"{file_path} was modified",
            passed=False,
            detail=f"file {file_path} does not exist",
        )
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        changed_files = result.stdout.strip().split("\n")
        was_changed = file_path in changed_files
        return AssertionResult(
            name=f"{file_path} was modified",
            passed=was_changed,
            detail=(
                "file was modified"
                if was_changed
                else (f"file unchanged. Changed: {changed_files}")
            ),
        )
    except Exception:
        return AssertionResult(
            name=f"{file_path} was modified",
            passed=False,
            detail="could not check git status",
        )


def check_read_to_edit_ratio_assertion(
    trace: SessionTrace,
    minimum_ratio: float,
) -> AssertionResult:
    tool_sequence = extract_tool_name_sequence(trace)
    read_count = tool_sequence.count("Read")
    edit_count = tool_sequence.count("Edit") + tool_sequence.count("Write")

    if edit_count == 0:
        return AssertionResult(
            name=f"read-to-edit ratio >= {minimum_ratio}",
            passed=False,
            detail="no edits made - agent did not act",
        )

    actual_ratio = read_count / edit_count
    passed = actual_ratio >= minimum_ratio
    return AssertionResult(
        name=f"read-to-edit ratio >= {minimum_ratio}",
        passed=passed,
        detail=(f"ratio {actual_ratio:.1f} ({read_count} reads / {edit_count} edits)"),
    )


def check_minimum_tool_count_assertion(
    trace: SessionTrace,
    tool_name: str,
    minimum_count: int,
) -> AssertionResult:
    tool_sequence = extract_tool_name_sequence(trace)
    actual_count = tool_sequence.count(tool_name)
    passed = actual_count >= minimum_count
    return AssertionResult(
        name=f"{tool_name} called >= {minimum_count} times",
        passed=passed,
        detail=f"called {actual_count} time(s)",
    )


def run_assertions(
    trace: SessionTrace,
    assertions: dict,
    workspace_directory: Path | None = None,
) -> list[AssertionResult]:
    results = []

    for ordering in assertions.get("tool_order", []):
        results.append(check_tool_ordering_assertion(trace, ordering))

    for required_tool in assertions.get("tool_presence", []):
        results.append(check_tool_presence_assertion(trace, required_tool))

    for forbidden_tool in assertions.get("tool_absence", []):
        results.append(check_tool_absence_assertion(trace, forbidden_tool))

    for expected in assertions.get("output_contains", []):
        results.append(check_output_contains_assertion(trace, expected))

    for forbidden in assertions.get("output_not_contains", []):
        results.append(check_output_not_contains_assertion(trace, forbidden))

    for forbidden in assertions.get("written_code_not_contains", []):
        results.append(check_written_code_not_contains_assertion(trace, forbidden))

    if workspace_directory:
        for file_check in assertions.get("file_not_contains", []):
            results.append(
                check_workspace_file_not_contains_assertion(
                    workspace_directory,
                    file_check["file"],
                    file_check["pattern"],
                )
            )

        for file_path in assertions.get("file_changed", []):
            results.append(
                check_workspace_file_changed_assertion(workspace_directory, file_path)
            )

    if "read_to_edit_ratio" in assertions:
        results.append(
            check_read_to_edit_ratio_assertion(trace, assertions["read_to_edit_ratio"])
        )

    for tool_count in assertions.get("minimum_tool_count", []):
        results.append(
            check_minimum_tool_count_assertion(
                trace,
                tool_count["tool"],
                tool_count["count"],
            )
        )

    return results


def sanitize_scenario_name_for_tempdir(
    scenario_name: str,
) -> str:
    return "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in scenario_name
    )


def run_scenario(
    scenario_path: Path,
    model: str = "sonnet",
    dry_run: bool = False,
) -> ScenarioResult:
    scenario = load_scenario(scenario_path)
    scenario_name = scenario["name"]

    if dry_run:
        return ScenarioResult(
            scenario_name=scenario_name,
            passed=True,
            assertion_results=[],
            trace=SessionTrace(),
            workspace_directory=None,
            duration_seconds=0,
        )

    sanitized_name = sanitize_scenario_name_for_tempdir(scenario_name)
    workspace_directory = Path(
        tempfile.mkdtemp(prefix=f"claude-eval-{sanitized_name}-")
    )

    try:
        setup_scenario_workspace(scenario, workspace_directory)

        system_prompt = scenario.get("system_prompt")
        if system_prompt is None:
            system_prompt = load_core_system_prompt()

        timeout = scenario.get("timeout", 180)

        prompt = scenario.get("prompt")
        if not prompt:
            return ScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=SessionTrace(),
                workspace_directory=workspace_directory,
                duration_seconds=0,
                error="Scenario missing 'prompt' field",
            )

        trace = run_claude_session(
            prompt=prompt,
            workspace_directory=workspace_directory,
            system_prompt=system_prompt,
            timeout_seconds=timeout,
            model=model,
        )

        if trace.exit_code == 124:
            return ScenarioResult(
                scenario_name=scenario_name,
                passed=False,
                assertion_results=[],
                trace=trace,
                workspace_directory=workspace_directory,
                duration_seconds=trace.duration_seconds,
                error=f"Session timed out after {timeout}s",
            )

        assertion_results = run_assertions(
            trace,
            scenario.get("assertions", {}),
            workspace_directory=workspace_directory,
        )
        all_passed = all(
            assertion_result.passed for assertion_result in assertion_results
        )

        return ScenarioResult(
            scenario_name=scenario_name,
            passed=all_passed,
            assertion_results=assertion_results,
            trace=trace,
            workspace_directory=workspace_directory,
            duration_seconds=trace.duration_seconds,
        )

    finally:
        shutil.rmtree(workspace_directory, ignore_errors=True)


def print_scenario_results(
    results: list[ScenarioResult],
) -> bool:
    print("\n" + "=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60 + "\n")

    all_passed = True

    for result in results:
        status_symbol = "\u2713" if result.passed else "\u2717"
        color = "\033[32m" if result.passed else "\033[31m"
        reset = "\033[0m"

        print(
            f"{color}{status_symbol}{reset} "
            f"{result.scenario_name} "
            f"({result.duration_seconds:.1f}s)"
        )

        if result.error:
            print(f"    Error: {result.error}")

        for assertion_result in result.assertion_results:
            assertion_symbol = "\u2713" if assertion_result.passed else "\u2717"
            assertion_color = "\033[32m" if assertion_result.passed else "\033[31m"
            print(
                f"    {assertion_color}{assertion_symbol}"
                f"{reset} "
                f"{assertion_result.name}: "
                f"{assertion_result.detail}"
            )

        if not result.passed:
            all_passed = False
            tool_sequence = extract_tool_name_sequence(result.trace)
            if tool_sequence:
                print(f"    Tool sequence: {' -> '.join(tool_sequence)}")

    passed_count = sum(1 for result in results if result.passed)
    print(f"\n{'=' * 60}")
    print(f"Passed: {passed_count}/{len(results)}")
    total_duration = sum(result.duration_seconds for result in results)
    print(f"Total time: {total_duration:.1f}s")
    print(f"{'=' * 60}\n")

    return all_passed


def discover_scenario_files(
    scenarios_directory: Path,
) -> list[Path]:
    return sorted(scenarios_directory.glob("*.yaml"))


def main():
    parser = argparse.ArgumentParser(
        description=("Run Claude Code integration tests with real sessions")
    )
    parser.add_argument(
        "--scenario",
        help="Run a specific scenario by name",
    )
    parser.add_argument(
        "--model",
        default="sonnet",
        help="Model to use for sessions (default: sonnet)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List scenarios without running them",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios",
    )
    parser.add_argument(
        "--scenarios-dir",
        default=SCENARIOS_DIR,
        type=Path,
        help="Directory containing scenario YAML files",
    )
    args = parser.parse_args()

    scenario_files = discover_scenario_files(args.scenarios_dir)

    if not scenario_files:
        print("No scenario files found in", args.scenarios_dir)
        sys.exit(1)

    if args.list:
        print("Available integration test scenarios:")
        for scenario_file in scenario_files:
            scenario = load_scenario(scenario_file)
            print(f"  {scenario['name']}: {scenario.get('description', '')}")
        sys.exit(0)

    if args.scenario:
        scenario_files = [
            scenario_file
            for scenario_file in scenario_files
            if load_scenario(scenario_file)["name"] == args.scenario
        ]
        if not scenario_files:
            print(f"Scenario '{args.scenario}' not found")
            sys.exit(1)

    if not args.dry_run:
        result = subprocess.run(["which", "claude"], capture_output=True)
        if result.returncode != 0:
            print("Error: claude CLI not found")
            sys.exit(1)

    results = []
    for scenario_file in scenario_files:
        result = run_scenario(
            scenario_file,
            model=args.model,
            dry_run=args.dry_run,
        )
        results.append(result)

    all_passed = print_scenario_results(results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
