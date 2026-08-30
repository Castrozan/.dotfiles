import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from run_evals_worktree_and_environment import (
    EVAL_WORKING_DIRECTORY,
    build_filtered_environment,
)

NODE_RUNTIME_OVERRIDE = "AGENT_EVAL_NODE_RUNTIME"
NODE_RUNTIME_BINARY = "agent-eval-provider"

ALLOWED_HARNESSES = ("claude", "codex", "opencode")

TRANSIENT_RETRY_ATTEMPTS = 2
TRANSIENT_RETRY_BACKOFF_SECONDS = 3
NON_RETRYABLE_FAILURE_MARKERS = (
    "cannot enforce no_tools",
    "session limit",
    "usage limit",
    "not logged in",
    'must be "provider/model"',
)
RESULT_WRITE_POLL_INTERVAL_SECONDS = 0.05
RESULT_WRITE_TIMEOUT_SECONDS = 5
RUNTIME_CLEANUP_GRACE_SECONDS = 5


def build_claude_judge_invoker(timeout: int = 120):
    def invoke(judge_prompt, model="opus", no_tools=False):
        return invoke_subject(
            "claude",
            prompt=judge_prompt,
            model=model,
            timeout=timeout,
            no_tools=no_tools,
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
    test: dict, harness: str, default_model: str | None
) -> str | None:
    named_models = test.get("models") or {}
    if harness in named_models:
        return named_models[harness]
    if harness == "claude":
        return test.get("model", default_model)
    return None


def build_subject_invocation(
    harness: str,
    *,
    prompt: str,
    model: str | None,
    system_prompt: str | None,
    timeout: int,
    no_tools: bool,
    working_directory: Path | None,
    result_file: str,
) -> dict:
    return {
        "harness": harness,
        "prompt": prompt,
        "model": model,
        "system_prompt": system_prompt,
        "working_directory": str(working_directory or EVAL_WORKING_DIRECTORY),
        "timeout": timeout,
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
        return {"output": None, "error": "the provider runtime produced no result file"}
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
    system_prompt: str | None = None,
    timeout: int = 120,
    no_tools: bool = False,
    working_directory: Path | None = None,
) -> tuple[str, bool]:
    runtime_command = resolve_node_runtime()

    with tempfile.TemporaryDirectory(prefix="agent-eval-result-") as result_directory:
        result_file_path = Path(result_directory) / "result.json"
        invocation = build_subject_invocation(
            harness=harness,
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            timeout=timeout,
            no_tools=no_tools,
            working_directory=working_directory,
            result_file=str(result_file_path),
        )
        last_transient_failure = ""
        for attempt in range(TRANSIENT_RETRY_ATTEMPTS + 1):
            result_file_path.unlink(missing_ok=True)
            try:
                subprocess.run(
                    [runtime_command],
                    input=json.dumps(invocation),
                    capture_output=True,
                    text=True,
                    timeout=timeout + RUNTIME_CLEANUP_GRACE_SECONDS,
                    cwd=working_directory or EVAL_WORKING_DIRECTORY,
                    env=build_filtered_environment(),
                )
            except subprocess.TimeoutExpired:
                last_transient_failure = f"timeout after {timeout}s"
            except FileNotFoundError:
                return "the node provider runtime was not found on PATH", False
            except Exception as error:
                return str(error), False
            else:
                result = read_result_file(result_file_path)
                error_text = result.get("error")
                output_text = result.get("output")
                if error_text is None:
                    normalized_output = "" if output_text is None else str(output_text)
                    if normalized_output.strip():
                        return normalized_output, True
                    error_text = "the provider runtime produced empty output"
                if not is_retryable_failure(error_text):
                    return error_text, False
                last_transient_failure = error_text

            if attempt < TRANSIENT_RETRY_ATTEMPTS:
                time.sleep(TRANSIENT_RETRY_BACKOFF_SECONDS * (attempt + 1))

        return last_transient_failure, False
