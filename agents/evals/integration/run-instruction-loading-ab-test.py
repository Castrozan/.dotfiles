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


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORE_INSTRUCTIONS_PATH = REPO_ROOT / "agents" / "core.md"


@dataclass
class ToolCallEvent:
    tool_name: str
    tool_input: dict


@dataclass
class SessionTrace:
    tool_calls: list[ToolCallEvent] = field(default_factory=list)
    assistant_messages: list[str] = field(default_factory=list)
    duration_seconds: float = 0
    exit_code: int = 0


@dataclass
class InstructionFollowingMetrics:
    read_before_edit: bool = False
    used_glob_not_find: bool = False
    no_comments_in_written_code: bool = False
    used_descriptive_names: bool = False
    used_specific_git_staging: bool = False
    read_to_edit_ratio: float = 0.0
    total_tool_calls: int = 0
    score: int = 0


@dataclass
class AbTestResult:
    configuration_name: str
    scenario_name: str
    metrics: InstructionFollowingMetrics
    trace: SessionTrace
    duration_seconds: float


def load_core_instructions_body() -> str:
    content = CORE_INSTRUCTIONS_PATH.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def load_core_instructions_with_frontmatter() -> str:
    return CORE_INSTRUCTIONS_PATH.read_text()


UNPROMPTED_SCENARIOS = [
    {
        "name": "edit_without_instruction_hints",
        "description": (
            "Edit task with NO mention of reading first, "
            "no comments, or naming conventions"
        ),
        "files": {
            "src/handler.py": (
                "def proc(d):\n"
                "    r = []\n"
                "    for i in d:\n"
                "        if i > 0:\n"
                "            r.append(i * 2)\n"
                "    return r\n"
            ),
        },
        "prompt": ("Refactor src/handler.py to be cleaner and more readable."),
    },
    {
        "name": "bug_fix_without_methodology_hints",
        "description": (
            "Bug fix with NO mention of investigating or reading files first"
        ),
        "files": {
            "app/service.py": (
                "from app.db import get_item\n\n"
                "def calculate_total(order_id):\n"
                "    items = get_item(order_id)\n"
                "    return sum(i['price'] for i in items)\n"
            ),
            "app/db.py": (
                "DATA = {\n"
                '    1: [{"name": "A", "price": 10}],\n'
                '    2: [{"name": "B", "price": 20}],\n'
                "}\n\n"
                "def get_item(order_id):\n"
                "    return DATA[order_id]\n"
            ),
        },
        "prompt": (
            "calculate_total crashes with KeyError when order_id is 999. Fix it."
        ),
    },
    {
        "name": "find_files_without_tool_hints",
        "description": ("File search with NO mention of which tool to use"),
        "files": {
            "src/main.py": 'print("hello")\n',
            "src/utils.py": "def helper(): pass\n",
            "lib/core.py": "class Core: pass\n",
            "tests/test_main.py": ("def test_main(): assert True\n"),
        },
        "prompt": ("What Python files exist in this project? List them."),
    },
]


def setup_workspace_with_reference_claude_md(
    workspace_directory: Path,
    files: dict[str, str],
) -> None:
    agents_md_path = workspace_directory / "AGENTS.md"
    agents_md_path.write_text(load_core_instructions_with_frontmatter())

    claude_md_path = workspace_directory / "CLAUDE.md"
    claude_md_path.write_text("@AGENTS.md\n")

    for relative_path, content in files.items():
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    initialize_git_repository(workspace_directory)


def setup_workspace_with_inline_claude_md(
    workspace_directory: Path,
    files: dict[str, str],
) -> None:
    full_instructions = load_core_instructions_body()

    claude_md_path = workspace_directory / "CLAUDE.md"
    claude_md_path.write_text(full_instructions + "\n")

    for relative_path, content in files.items():
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    initialize_git_repository(workspace_directory)


def setup_workspace_with_system_prompt(
    workspace_directory: Path,
    files: dict[str, str],
) -> None:
    for relative_path, content in files.items():
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    initialize_git_repository(workspace_directory)


def setup_workspace_with_no_instructions(
    workspace_directory: Path,
    files: dict[str, str],
) -> None:
    for relative_path, content in files.items():
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    initialize_git_repository(workspace_directory)


def initialize_git_repository(
    workspace_directory: Path,
) -> None:
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
        env=git_env,
    )


def run_claude_session_without_system_prompt(
    prompt: str,
    workspace_directory: Path,
    timeout_seconds: int = 120,
    model: str = "haiku",
) -> SessionTrace:
    command = [
        "claude",
        "-p",
        "--verbose",
        "--output-format",
        "stream-json",
        "--model",
        model,
        prompt,
    ]

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
            duration_seconds=time.time() - start_time,
            exit_code=124,
        )

    trace = parse_stream_json_output(result.stdout)
    trace.duration_seconds = time.time() - start_time
    trace.exit_code = result.returncode
    return trace


def run_claude_session_with_system_prompt(
    prompt: str,
    workspace_directory: Path,
    system_prompt: str,
    timeout_seconds: int = 120,
    model: str = "haiku",
) -> SessionTrace:
    command = [
        "claude",
        "-p",
        "--verbose",
        "--output-format",
        "stream-json",
        "--model",
        model,
        "--system-prompt",
        system_prompt,
        prompt,
    ]

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
            duration_seconds=time.time() - start_time,
            exit_code=124,
        )

    trace = parse_stream_json_output(result.stdout)
    trace.duration_seconds = time.time() - start_time
    trace.exit_code = result.returncode
    return trace


def parse_stream_json_output(
    raw_output: str,
) -> SessionTrace:
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
            message = event.get("message", event)
            content_blocks = message.get("content", [])
            if not isinstance(content_blocks, list):
                continue
            for block in content_blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    trace.tool_calls.append(
                        ToolCallEvent(
                            tool_name=block.get("name", ""),
                            tool_input=block.get("input", {}),
                        )
                    )
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text.strip():
                        trace.assistant_messages.append(text)

        if event_type == "result":
            result_text = event.get("result", "")
            if isinstance(result_text, str):
                trace.assistant_messages.append(result_text)

    return trace


def extract_tool_names(
    trace: SessionTrace,
) -> list[str]:
    return [tc.tool_name for tc in trace.tool_calls]


def collect_written_content(
    trace: SessionTrace,
) -> str:
    parts = []
    for tc in trace.tool_calls:
        if tc.tool_name in ("Edit", "Write"):
            new_string = tc.tool_input.get("new_string", "")
            content = tc.tool_input.get("content", "")
            if new_string:
                parts.append(new_string)
            if content:
                parts.append(content)
    return "\n".join(parts)


ABBREVIATION_PATTERNS = [
    "def proc(",
    "def fmt(",
    "def calc(",
    "def chk(",
    "def fn(",
    "def f(",
    "def g(",
    "def h(",
]


def measure_instruction_following(
    trace: SessionTrace,
) -> InstructionFollowingMetrics:
    metrics = InstructionFollowingMetrics()
    tool_names = extract_tool_names(trace)
    metrics.total_tool_calls = len(tool_names)

    read_count = tool_names.count("Read")
    edit_count = tool_names.count("Edit") + tool_names.count("Write")
    glob_count = tool_names.count("Glob")
    grep_count = tool_names.count("Grep")

    if edit_count > 0 and read_count > 0:
        first_read = next(
            (i for i, name in enumerate(tool_names) if name == "Read"),
            999,
        )
        first_edit = next(
            (i for i, name in enumerate(tool_names) if name in ("Edit", "Write")),
            999,
        )
        metrics.read_before_edit = first_read < first_edit
        metrics.read_to_edit_ratio = read_count / edit_count
    elif edit_count > 0:
        metrics.read_before_edit = False
        metrics.read_to_edit_ratio = 0.0

    has_bash_find = any(
        tc.tool_name == "Bash" and "find " in tc.tool_input.get("command", "")
        for tc in trace.tool_calls
    )
    metrics.used_glob_not_find = (
        glob_count > 0 or grep_count > 0
    ) and not has_bash_find

    written_content = collect_written_content(trace)
    if written_content:
        has_comments = any(
            pattern in written_content for pattern in ("# ", "// ", "/* ")
        )
        metrics.no_comments_in_written_code = not has_comments

        has_abbreviations = any(
            pattern in written_content for pattern in ABBREVIATION_PATTERNS
        )
        metrics.used_descriptive_names = not has_abbreviations
    else:
        metrics.no_comments_in_written_code = True
        metrics.used_descriptive_names = True

    has_git_add_all = any(
        tc.tool_name == "Bash"
        and (
            "git add -A" in tc.tool_input.get("command", "")
            or "git add ." in tc.tool_input.get("command", "")
        )
        for tc in trace.tool_calls
    )
    has_git_add_specific = any(
        tc.tool_name == "Bash"
        and "git add " in tc.tool_input.get("command", "")
        and "git add -A" not in tc.tool_input.get("command", "")
        and "git add ." not in tc.tool_input.get("command", "")
        for tc in trace.tool_calls
    )
    metrics.used_specific_git_staging = (
        has_git_add_specific and not has_git_add_all
    ) or not has_git_add_all

    score = 0
    if metrics.read_before_edit:
        score += 20
    if metrics.read_to_edit_ratio >= 1.0:
        score += 15
    elif metrics.read_to_edit_ratio >= 0.5:
        score += 8
    if metrics.used_glob_not_find:
        score += 15
    if metrics.no_comments_in_written_code:
        score += 20
    if metrics.used_descriptive_names:
        score += 15
    if metrics.used_specific_git_staging:
        score += 15
    metrics.score = min(score, 100)

    return metrics


CONFIGURATION_SETUP_FUNCTIONS = {
    "reference": setup_workspace_with_reference_claude_md,
    "inline": setup_workspace_with_inline_claude_md,
    "system-prompt": setup_workspace_with_system_prompt,
    "no-instructions": setup_workspace_with_no_instructions,
}


def run_ab_test_for_scenario(
    scenario: dict,
    configurations: list[str],
    model: str = "haiku",
) -> list[AbTestResult]:
    results = []

    for configuration_name in configurations:
        workspace_directory = Path(
            tempfile.mkdtemp(prefix=(f"ab-{configuration_name}-{scenario['name']}-"))
        )

        try:
            setup_function = CONFIGURATION_SETUP_FUNCTIONS[configuration_name]
            setup_function(workspace_directory, scenario["files"])

            if configuration_name == "system-prompt":
                trace = run_claude_session_with_system_prompt(
                    prompt=scenario["prompt"],
                    workspace_directory=workspace_directory,
                    system_prompt=load_core_instructions_body(),
                    model=model,
                )
            else:
                trace = run_claude_session_without_system_prompt(
                    prompt=scenario["prompt"],
                    workspace_directory=workspace_directory,
                    model=model,
                )

            metrics = measure_instruction_following(trace)

            results.append(
                AbTestResult(
                    configuration_name=configuration_name,
                    scenario_name=scenario["name"],
                    metrics=metrics,
                    trace=trace,
                    duration_seconds=trace.duration_seconds,
                )
            )

        finally:
            shutil.rmtree(workspace_directory, ignore_errors=True)

    return results


def print_ab_test_results(
    all_results: list[AbTestResult],
    configurations: list[str],
) -> None:
    print("\n" + "=" * 70)
    print("INSTRUCTION LOADING A/B TEST - UNPROMPTED INSTRUCTION FOLLOWING")
    print("=" * 70)

    scenario_names = list(dict.fromkeys(result.scenario_name for result in all_results))

    header = f"{'Metric':<30}"
    for config_name in configurations:
        header += f" {config_name:>14}"
    print(f"\n{header}")
    print("-" * (30 + 15 * len(configurations)))

    for scenario_name in scenario_names:
        print(f"\n  Scenario: {scenario_name}")
        scenario_results = {
            result.configuration_name: result
            for result in all_results
            if result.scenario_name == scenario_name
        }

        metrics_to_display = [
            ("read_before_edit", "Read before edit"),
            ("used_glob_not_find", "Glob over find"),
            (
                "no_comments_in_written_code",
                "No comments in code",
            ),
            (
                "used_descriptive_names",
                "Descriptive names",
            ),
            (
                "used_specific_git_staging",
                "Specific git staging",
            ),
            ("read_to_edit_ratio", "Read/edit ratio"),
            ("score", "SCORE"),
        ]

        for metric_key, metric_label in metrics_to_display:
            row = f"  {metric_label:<28}"
            for config_name in configurations:
                result = scenario_results.get(config_name)
                if result:
                    value = getattr(result.metrics, metric_key)
                    if isinstance(value, bool):
                        symbol = "\033[32mYES\033[0m" if value else "\033[31m NO\033[0m"
                        row += f" {symbol:>23}"
                    elif isinstance(value, float):
                        row += f" {value:>14.1f}"
                    else:
                        row += f" {value:>14}"
                else:
                    row += f" {'N/A':>14}"
            print(row)

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("-" * 70)

    for config_name in configurations:
        config_results = [
            result for result in all_results if result.configuration_name == config_name
        ]
        if not config_results:
            continue
        average_score = sum(result.metrics.score for result in config_results) / len(
            config_results
        )
        total_duration = sum(result.duration_seconds for result in config_results)
        score_color = (
            "\033[32m"
            if average_score >= 60
            else "\033[33m"
            if average_score >= 40
            else "\033[31m"
        )
        print(
            f"  {config_name:<20} "
            f"avg score: {score_color}"
            f"{average_score:.0f}/100\033[0m  "
            f"time: {total_duration:.0f}s"
        )

    print(f"{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "A/B test: does CLAUDE.md @ reference vs "
            "inline content affect instruction following?"
        )
    )
    parser.add_argument(
        "--model",
        default="haiku",
        help="Model to use (default: haiku)",
    )
    parser.add_argument(
        "--configurations",
        nargs="+",
        default=[
            "reference",
            "inline",
            "system-prompt",
            "no-instructions",
        ],
        help="Configurations to test",
    )
    parser.add_argument(
        "--scenario",
        help="Run specific scenario only",
    )
    args = parser.parse_args()

    result = subprocess.run(["which", "claude"], capture_output=True)
    if result.returncode != 0:
        print("Error: claude CLI not found")
        sys.exit(1)

    scenarios_to_run = UNPROMPTED_SCENARIOS
    if args.scenario:
        scenarios_to_run = [
            scenario
            for scenario in UNPROMPTED_SCENARIOS
            if scenario["name"] == args.scenario
        ]
        if not scenarios_to_run:
            print(f"Scenario '{args.scenario}' not found")
            sys.exit(1)

    all_results = []
    for scenario in scenarios_to_run:
        print(f"Running: {scenario['name']}...")
        results = run_ab_test_for_scenario(
            scenario,
            args.configurations,
            model=args.model,
        )
        all_results.extend(results)

    print_ab_test_results(all_results, args.configurations)


if __name__ == "__main__":
    main()
