import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path

from runner import run_evals_worktree_and_environment as evaluation_environment
from runner.execution import run_evals_subject_runtime as subject_runtime

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


@dataclass(frozen=True)
class SubjectRequest:
    prompt: str
    model: str | None = None
    model_reasoning_effort: str | None = None
    system_prompt: str | None = None
    timeout: int = 120
    max_turns: int | None = None
    no_tools: bool = False
    working_directory: Path | None = None
    isolated_context: bool = False


def build_provider_invoker(
    harness: str,
    timeout: int = 120,
    model_reasoning_effort: str | None = None,
):
    def invoke(judge_prompt, model="opus", no_tools=False):
        return invoke_subject(
            harness,
            SubjectRequest(
                prompt=judge_prompt,
                model=model,
                model_reasoning_effort=model_reasoning_effort,
                timeout=timeout,
                max_turns=1,
                no_tools=no_tools,
                isolated_context=True,
            ),
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
    harness: str, request: SubjectRequest, result_file: str
) -> dict:
    return {
        "harness": harness,
        "prompt": request.prompt,
        "model": request.model,
        "model_reasoning_effort": request.model_reasoning_effort,
        "system_prompt": request.system_prompt,
        "working_directory": str(
            request.working_directory or evaluation_environment.EVAL_WORKING_DIRECTORY
        ),
        "timeout": request.timeout,
        "max_turns": request.max_turns,
        "no_tools": request.no_tools,
        "result_file": result_file,
        "isolated_context": request.isolated_context,
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
    harness: str, request: SubjectRequest, invocation_role: str = "subject"
) -> tuple[str, bool]:
    runtime_command = resolve_node_runtime()

    with (
        tempfile.TemporaryDirectory(prefix="agent-eval-result-") as result_directory,
        tempfile.TemporaryDirectory(prefix="agent-eval-isolated-") as empty_directory,
    ):
        if request.isolated_context:
            request = replace(request, working_directory=Path(empty_directory))
        result_file_path = Path(result_directory) / "result.json"
        invocation = build_subject_invocation(harness, request, str(result_file_path))
        runtime_options = subject_runtime.SubjectRuntimeOptions(
            runtime_command,
            invocation_role,
            harness,
            evaluation_environment.build_filtered_environment,
            subprocess,
        )
        return subject_runtime.invoke_prepared_subject(
            invocation,
            runtime_options,
            read_result_file,
            is_retryable_failure,
        )
