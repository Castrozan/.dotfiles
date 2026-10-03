import json
from dataclasses import dataclass
from types import ModuleType
import time
from pathlib import Path
from typing import Callable

from runner.execution.run_evals_provider_usage import (
    record_provider_invocation,
    record_provider_usage,
)

TRANSIENT_RETRY_ATTEMPTS = 2
TRANSIENT_RETRY_BACKOFF_SECONDS = 3
RUNTIME_CLEANUP_GRACE_SECONDS = 5


@dataclass(frozen=True)
class SubjectRuntimeOptions:
    runtime_command: str
    invocation_role: str
    harness: str
    read_environment: Callable
    subprocess_module: ModuleType


def invoke_prepared_subject(
    invocation: dict,
    options: SubjectRuntimeOptions,
    read_result_file,
    is_retryable_failure,
) -> tuple[str, bool]:
    result_file_path = invocation["result_file"]
    last_transient_failure = ""
    for attempt in range(TRANSIENT_RETRY_ATTEMPTS + 1):
        result_file_path_object = Path(result_file_path)
        result_file_path_object.unlink(missing_ok=True)
        record_provider_invocation(options.invocation_role, options.harness)
        try:
            options.subprocess_module.run(
                [options.runtime_command],
                input=json.dumps(invocation),
                capture_output=True,
                text=True,
                timeout=invocation["timeout"] + RUNTIME_CLEANUP_GRACE_SECONDS,
                cwd=invocation["working_directory"],
                env=options.read_environment(),
            )
        except options.subprocess_module.TimeoutExpired:
            last_transient_failure = f"timeout after {invocation['timeout']}s"
        except FileNotFoundError:
            return "the node provider runtime was not found on PATH", False
        except Exception as error:
            return str(error), False
        else:
            result = read_result_file(result_file_path_object)
            record_provider_usage(
                options.invocation_role, options.harness, result.get("usage")
            )
            normalized_output, error_text = _normalize_runtime_result(result)
            if error_text is None:
                return normalized_output, True
            if not is_retryable_failure(error_text):
                return error_text, False
            last_transient_failure = error_text

        if attempt < TRANSIENT_RETRY_ATTEMPTS:
            time.sleep(TRANSIENT_RETRY_BACKOFF_SECONDS * (attempt + 1))

    return last_transient_failure, False


def _normalize_runtime_result(result: dict) -> tuple[str, str | None]:
    error_text = result.get("error")
    output_text = result.get("output")
    if error_text is not None:
        return "", error_text
    normalized_output = "" if output_text is None else str(output_text)
    if normalized_output.strip():
        return normalized_output, None
    return "", "the provider runtime produced empty output"
