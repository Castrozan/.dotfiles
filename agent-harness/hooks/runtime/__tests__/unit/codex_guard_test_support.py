import json
import os

from flat_deploy_test_support import (
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)

CODEX_SURFACE_ARGUMENT = "--surface=codex"


def run_codex_pre_tool_use_dispatcher(tmp_path, payload, environment=None):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    return run_flattened_hook(
        runtime_directory,
        "pre-tool-use-dispatcher.py",
        payload,
        environment
        if environment is not None
        else {**os.environ, "TMPDIR": str(tmp_path), "HOME": str(tmp_path)},
        (CODEX_SURFACE_ARGUMENT,),
    )


def permission_decision_of(result):
    if not result.stdout.strip():
        return None
    emitted = json.loads(result.stdout)
    return emitted.get("hookSpecificOutput", {}).get("permissionDecision")
