import json
import shutil
import subprocess
import sys
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

HOOKS_ROOT = Path(__file__).resolve().parents[2]

DEPLOYED_HOOK_SCRIPT_SUFFIXES = (".py", ".sh", ".md")
DIRECTORIES_EXCLUDED_FROM_DEPLOY = ("__pycache__", "__tests__")

INTERACTIVE_ENV_VAR = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENV_MARKER = "CLAWDE_AGENT_NAME"
REMINDER_STATE_DIRECTORY_ENV_VAR = "INTERACTIVE_REPLY_REMINDER_STATE_DIRECTORY"


def every_deployed_hook_script():
    return [
        candidate
        for candidate in HOOKS_ROOT.rglob("*")
        if candidate.is_file()
        and candidate.suffix in DEPLOYED_HOOK_SCRIPT_SUFFIXES
        and not any(
            excluded in candidate.parts for excluded in DIRECTORIES_EXCLUDED_FROM_DEPLOY
        )
    ]


def flatten_into_single_runtime_directory(directory, source_files=None):
    for source_file in (
        source_files if source_files is not None else every_deployed_hook_script()
    ):
        shutil.copy(source_file, directory / source_file.name)


def run_flattened_hook(
    directory, hook_filename, payload, environment, extra_arguments=()
):
    return subprocess.run(
        [sys.executable, str(directory / hook_filename), *extra_arguments],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
        env=environment,
    )
