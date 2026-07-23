import subprocess
import time

import run_evals_worktree_and_environment
from run_evals_worktree_and_environment import build_filtered_environment

TRANSIENT_RETRY_ATTEMPTS = 2
TRANSIENT_RETRY_BACKOFF_SECONDS = 3


def run_claude_cli(
    prompt: str,
    model: str = "sonnet",
    system_prompt: str | None = None,
    timeout: int = 120,
    no_tools: bool = False,
) -> tuple[str, bool]:
    cmd = ["claude", "-p", "--model", model, "--strict-mcp-config"]

    if no_tools:
        cmd.extend(["--tools", ""])

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    last_transient_failure = ""
    for attempt in range(TRANSIENT_RETRY_ATTEMPTS + 1):
        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=run_evals_worktree_and_environment.EVAL_WORKING_DIRECTORY,
                env=build_filtered_environment(),
            )
            combined_output = result.stdout + result.stderr
            if result.returncode == 0 and combined_output.strip():
                return combined_output, True
            last_transient_failure = (
                combined_output or f"empty output (exit {result.returncode})"
            )
        except subprocess.TimeoutExpired:
            last_transient_failure = f"Timeout after {timeout}s"
        except FileNotFoundError:
            return "claude CLI not found - run 'rebuild' first", False
        except Exception as e:
            return str(e), False
        if attempt < TRANSIENT_RETRY_ATTEMPTS:
            time.sleep(TRANSIENT_RETRY_BACKOFF_SECONDS * (attempt + 1))
    return last_transient_failure, False
