import os
import subprocess
import sys
from pathlib import Path

from wait_for_event.process_exit_wait import every_process_exits_within

SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
TIMED_OUT_EXIT_CODE = 124


def start_wait_for_event(*arguments):
    return subprocess.Popen(
        [sys.executable, "-m", "wait_for_event", *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONPATH": str(SCRIPTS_DIRECTORY)},
    )


def child_blocked_on_its_input():
    return subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdin.read()"], stdin=subprocess.PIPE
    )


def test_a_line_already_in_the_file_is_printed_at_once(tmp_path):
    log_path = tmp_path / "rebuild.log"
    log_path.write_text("building\nREBUILD_EXIT=0\n")

    waiter = start_wait_for_event("file", str(log_path), "--match", r"REBUILD_EXIT=\d")
    output, _ = waiter.communicate(timeout=20)

    assert waiter.returncode == 0
    assert output == "REBUILD_EXIT=0\n"


def test_a_line_appended_after_the_wait_began_ends_it(tmp_path):
    log_path = tmp_path / "server.log"
    log_path.write_text("starting\n")
    waiter = start_wait_for_event(
        "file", str(log_path), "--match", "Listening", "--timeout-seconds", "20"
    )

    with log_path.open("a") as log_file:
        log_file.write("warming caches\nListening on :8080\n")
    output, _ = waiter.communicate(timeout=20)

    assert waiter.returncode == 0
    assert output == "Listening on :8080\n"


def test_a_file_that_never_matches_times_out_and_leaves_no_follower(tmp_path):
    log_path = tmp_path / "quiet.log"
    log_path.write_text("nothing here\n")

    waiter = start_wait_for_event(
        "file", str(log_path), "--match", "DONE", "--timeout-seconds", "0.3"
    )
    _, errors = waiter.communicate(timeout=20)

    assert waiter.returncode == TIMED_OUT_EXIT_CODE
    assert "timed out" in errors
    followers = subprocess.run(
        ["pgrep", "-f", f"tail -F -n \\+1 {log_path}"],
        capture_output=True,
        timeout=10,
    )
    assert followers.stdout == b""


def test_a_running_process_holds_the_wait_until_it_exits():
    child = child_blocked_on_its_input()

    assert not every_process_exits_within([child.pid], 0.2)
    child.stdin.close()
    assert every_process_exits_within([child.pid], 20)
    child.wait()


def test_a_process_that_is_already_gone_returns_at_once():
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()

    assert every_process_exits_within([child.pid], 0)


def test_the_command_line_reports_exit_and_timeout():
    child = child_blocked_on_its_input()

    waiter = start_wait_for_event("process", str(child.pid), "--timeout-seconds", "0.2")
    waiter.communicate(timeout=20)
    assert waiter.returncode == TIMED_OUT_EXIT_CODE

    waiter = start_wait_for_event("process", str(child.pid))
    child.stdin.close()
    output, _ = waiter.communicate(timeout=20)
    child.wait()
    assert waiter.returncode == 0
    assert output == f"exited {child.pid}\n"
