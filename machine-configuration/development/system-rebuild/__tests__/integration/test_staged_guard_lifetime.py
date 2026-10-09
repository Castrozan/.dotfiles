import os
import signal
import subprocess
import time

import pytest

from staged_rebuild_support import (
    SCRIPTS,
    build_staged_environment,
    read_events,
    write_prepared_request,
)
from test_managed_rebuild_lock import wait_for_path


@pytest.mark.parametrize("phase", ["evaluation", "activation"])
@pytest.mark.parametrize("termination_target", ["client", "pipeline"])
@pytest.mark.parametrize("termination_signal", [signal.SIGTERM, signal.SIGKILL])
def test_staged_client_death_retains_lock_until_close_fds_descendant_finishes(
    managed_rebuild_environment, tmp_path, phase, termination_target, termination_signal
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    environment.update(
        DOTFILES_REBUILD_WRAPPER="1",
        REAL_NIXOS_REBUILD=str(SCRIPTS / "staged-rebuild"),
    )
    environment[
        "TEST_EVAL_HOLD" if phase == "evaluation" else "TEST_ACTIVATION_HOLD"
    ] = "1"
    request = write_prepared_request(tmp_path, "boot")
    log = (tmp_path / "guard-output").open("w")
    holder = subprocess.Popen(
        [str(SCRIPTS.parent / "nixos-rebuild-guard"), "boot", str(request)],
        env=environment,
        stdout=log,
        stderr=log,
        start_new_session=True,
    )
    process_group = None
    try:
        started = (
            "descendant-started"
            if phase == "evaluation"
            else "activation-descendant-started"
        )
        pid_file = "eval-pid" if phase == "evaluation" else "activation-pid"
        wait_for_path(tmp_path / started)
        client = int((tmp_path / pid_file).read_text())
        process_group = os.getpgid(client)
        target = client if termination_target == "client" else process_group
        os.kill(target, termination_signal)
        contender = subprocess.run(
            [environment["SYSTEM_REBUILD_LOCK_GUARD"], "true"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert contender.returncode == 99, contender.stderr
        assert "LOCKED_BY_CONCURRENT_RUN" in contender.stderr
        expected = [] if phase == "evaluation" else ["profile"]
        assert [
            event["phase"] for event in read_events(tmp_path, "native-events")
        ] == expected
        (tmp_path / "release-descendant").touch()
        assert holder.wait(timeout=5) == 128 + termination_signal
        deadline = time.monotonic() + 5
        while True:
            contender = subprocess.run(
                [environment["SYSTEM_REBUILD_LOCK_GUARD"], "true"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if contender.returncode == 0:
                break
            assert time.monotonic() < deadline
            time.sleep(0.01)
        completed_phases = (
            ["profile", "activate"]
            if phase == "activation" and termination_target == "pipeline"
            else expected
        )
        assert [
            event["phase"] for event in read_events(tmp_path, "native-events")
        ] == completed_phases
        if completed_phases == ["profile", "activate"]:
            assert read_events(tmp_path, "native-events")[-1]["action"] == "boot"
        if phase == "evaluation":
            assert not any(
                any(argument.endswith(".drv") for argument in event["arguments"])
                and "--realise" in event["arguments"]
                for event in read_events(tmp_path)
            )
    finally:
        (tmp_path / "release-descendant").touch()
        if process_group is not None:
            try:
                os.killpg(process_group, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if holder.poll() is None:
            holder.kill()
            holder.wait(timeout=5)
        log.close()
