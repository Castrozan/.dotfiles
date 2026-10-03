import json
import os
import shutil
import tempfile
import time
from pathlib import Path

from runner import run_evals_worktree_and_environment as evaluation_environment
from runner.execution import run_evals_subject_runtime as subject_runtime

subprocess = subject_runtime.subprocess

NODE_RUNTIME_OVERRIDE = "AGENT_EVAL_NODE_RUNTIME"
NODE_RUNTIME_BINARY = "agent-eval-provider"

ALLOWED_HARNESSES = ("claude", "codex", "opencode")

NON_RETRYABLE_FAILURE_MARKERS = (
    "session limit",
    "usage limit",
    "not logged in",
    'must be "provider/model"',
)
RESULT_WRITE_POLL_INTERVAL_SECONDS = 0.05
RESULT_WRITE_TIMEOUT_SECONDS = 5


def build_provider_invoker(
    harness: str,
    timeout: int = 120,
    model_reasoning_effort: str | None = None,
):
    def invoke(judge_prompt, model="opus", no_tools=False):
        return invoke_subject(
            harness,
            prompt=judge_prompt,
            model=model,
            model_reasoning_effort=model_reasoning_effort,
            timeout=timeout,
            max_turns=1,
            no_tools=no_tools,
            invocation_role="judge",
        )

    return invoke


def is_retryable_failure(output: str) -> bool:
    lowered = output.lower()
    return not any(marker in lowered for marker in NON_RETRYABLE_FAILURE_MARKERS)


def resolve_node_runtime() -> str:
    override = os.environ.get(NODE_RUNTIME_OVERRIDE, "")
    if override:
        return override
    resolved = shutil.which(NODE_RUNTIME_BINARY)
    if resolved is None:
        raise RuntimeError(
            "the packaged node provider runtime is not on PATH; run the packaged "
            f"agent-eval command or point {NODE_RUNTIME_OVERRIDE} at the runtime wrapper"
        )
    return resolved


def model_for_harness(
    test: dict, harness: str, default_models: dict[str, str]
) -> str | None:
    named_models = test.get("models") or {}
    if harness in named_models:
        return named_models[harness]
    if harness == "claude":
        return test.get("model", default_models.get(harness))
    return default_models.get(harness)


def build_subject_invocation(
    harness: str,
    *,
    prompt: str,
    model: str | None,
    model_reasoning_effort: str | None,
    system_prompt: str | None,
    timeout: int,
    max_turns: int | None,
    no_tools: bool,
    working_directory: Path | None,
    result_file: str,
) -> dict:
    return {
        "harness": harness,
        "prompt": prompt,
        "model": model,
        "model_reasoning_effort": model_reasoning_effort,
        "system_prompt": system_prompt,
        "working_directory": str(
            working_directory or evaluation_environment.EVAL_WORKING_DIRECTORY
        ),
        "timeout": timeout,
        "max_turns": max_turns,
        "no_tools": no_tools,
        "result_file": result_file,
    }


def read_result_file(result_file_path: Path) -> dict:
    deadline = time.monotonic() + RESULT_WRITE_TIMEOUT_SECONDS
    while not result_file_path.exists():
        if time.monotonic() >= deadline:
            break
        time.sleep(RESULT_WRITE_POLL_INTERVAL_SECONDS)
    if not result_file_path.exists():
        return {
            "output": None,
            "error": "the provider runtime produced no result file",
        }
    try:
        with result_file_path.open(encoding="utf-8") as result_file:
            return json.load(result_file)
    except (OSError, json.JSONDecodeError) as error:
        return {
            "output": None,
            "error": f"the provider runtime produced an invalid result: {error}",
        }


def invoke_subject(
    harness: str,
    *,
    prompt: str,
    model: str | None = None,
    model_reasoning_effort: str | None = None,
    system_prompt: str | None = None,
    timeout: int = 120,
    max_turns: int | None = None,
    no_tools: bool = False,
    working_directory: Path | None = None,
    invocation_role: str = "subject",
) -> tuple[str, bool]:
    runtime_command = resolve_node_runtime()

    with tempfile.TemporaryDirectory(prefix="agent-eval-result-") as result_directory:
        result_file_path = Path(result_directory) / "result.json"
        invocation = build_subject_invocation(
            harness=harness,
            prompt=prompt,
            model=model,
            model_reasoning_effort=model_reasoning_effort,
            system_prompt=system_prompt,
            timeout=timeout,
            max_turns=max_turns,
            no_tools=no_tools,
            working_directory=working_directory,
            result_file=str(result_file_path),
        )
        return subject_runtime.invoke_prepared_subject(
            invocation,
            runtime_command,
            invocation_role,
            harness,
            read_result_file,
            is_retryable_failure,
            evaluation_environment.build_filtered_environment,
        )
