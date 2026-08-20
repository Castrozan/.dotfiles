import json
import os
import subprocess
import sys
from pathlib import Path

from flat_deploy_test_support import (
    CLAWDE_BACKGROUND_AGENT_ENV_MARKER,
    INTERACTIVE_ENV_VAR,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_session_start_dispatcher_injects_no_servant_context(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    injected = run_flattened_hook(
        runtime_directory,
        "session-start-dispatcher.py",
        {
            "hook_event_name": "SessionStart",
            "session_id": "servant-flat-probe",
            "cwd": str(tmp_path),
        },
        {
            "HOME": str(tmp_path),
            "TMPDIR": str(tmp_path),
            INTERACTIVE_ENV_VAR: "/nix/store/preferences.md",
        },
    )
    assert injected.returncode == 0
    payload = json.loads(injected.stdout)
    assert payload["continue"] is True
    injected_context = payload.get("hookSpecificOutput", {}).get(
        "additionalContext", ""
    )
    assert "SERVANT" not in injected_context


def _run_flattened_summoner(runtime_directory, base_prompt_path, tmp_path, *arguments):
    return subprocess.run(
        [
            sys.executable,
            str(runtime_directory / "summon_servant.py"),
            str(base_prompt_path),
            *arguments,
        ],
        capture_output=True,
        text=True,
        env={
            "PATH": os.environ["PATH"],
            "TMPDIR": str(tmp_path),
            "HOME": str(tmp_path),
        },
        check=False,
    )


def _exports_of(completed_process):
    return dict(
        line.split("=", 1) for line in completed_process.stdout.strip().splitlines()
    )


def test_summon_servant_composes_a_prompt_after_flat_deploy(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    base_prompt_path = tmp_path / "base.md"
    base_prompt_path.write_text("<interactive>base rules</interactive>\n")

    summoned = _run_flattened_summoner(runtime_directory, base_prompt_path, tmp_path)
    assert summoned.returncode == 0
    exports = _exports_of(summoned)
    assert exports["SERVANT_NAME"].strip("'")
    composed_path = Path(exports["SERVANT_SYSTEM_PROMPT_FILE"].strip("'"))
    composed_text = composed_path.read_text()
    assert "<interactive>base rules</interactive>" in composed_text
    assert "<servant>You are " in composed_text


def test_summon_servant_keeps_one_servant_across_a_resume_after_flat_deploy(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)
    base_prompt_path = tmp_path / "base.md"
    base_prompt_path.write_text("<interactive>base rules</interactive>\n")

    launched = _exports_of(
        _run_flattened_summoner(runtime_directory, base_prompt_path, tmp_path)
    )
    minted_session_id = launched["SERVANT_SESSION_ID"].strip("'")
    assert minted_session_id

    resumed = _exports_of(
        _run_flattened_summoner(
            runtime_directory,
            base_prompt_path,
            tmp_path,
            "--resume",
            minted_session_id,
        )
    )
    assert resumed["SERVANT_NAME"] == launched["SERVANT_NAME"]
    assert resumed["SERVANT_SESSION_ID"] == "''"


def test_session_start_dispatcher_stays_silent_for_clawde_agent_after_flat_deploy(
    tmp_path,
):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    silent = run_flattened_hook(
        runtime_directory,
        "session-start-dispatcher.py",
        {
            "hook_event_name": "SessionStart",
            "session_id": "servant-flat-clawde-probe",
            "cwd": str(tmp_path),
        },
        {
            "HOME": str(tmp_path),
            "TMPDIR": str(tmp_path),
            INTERACTIVE_ENV_VAR: "/nix/store/preferences.md",
            CLAWDE_BACKGROUND_AGENT_ENV_MARKER: "steward",
        },
    )
    assert silent.returncode == 0
    assert "SERVANT" not in silent.stdout
