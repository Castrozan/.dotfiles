import threading

from background_commands import BACKGROUND_FAILURE_MESSAGE, BackgroundCommandRunner

COMMAND_TEXT = "hey clever what is the weather"
RELEASE_TIMEOUT_SECONDS = 5


def test_an_in_flight_command_is_awaited_instead_of_dropped_at_shutdown():
    released = threading.Event()
    completed = []

    def slow_command(command_text):
        released.wait(timeout=RELEASE_TIMEOUT_SECONDS)
        completed.append(command_text)

    runner = BackgroundCommandRunner(
        run_command=slow_command, report_failure=lambda _message: None
    )
    runner.start(COMMAND_TEXT)
    assert completed == []

    released.set()
    runner.wait_for_completion()

    assert completed == [COMMAND_TEXT]


def test_a_failing_command_is_reported_instead_of_killing_the_daemon():
    failures = []

    def failing_command(_command_text):
        raise RuntimeError("the gateway exploded")

    runner = BackgroundCommandRunner(
        run_command=failing_command, report_failure=failures.append
    )
    runner.start(COMMAND_TEXT)
    runner.wait_for_completion()

    assert failures == [f"{BACKGROUND_FAILURE_MESSAGE}: the gateway exploded"]


def test_finished_commands_are_forgotten_so_the_daemon_holds_no_thread_backlog():
    runner = BackgroundCommandRunner(
        run_command=lambda _command_text: None, report_failure=lambda _message: None
    )
    for _repetition in range(5):
        runner.start(COMMAND_TEXT)
        runner.wait_for_completion()

    runner.start(COMMAND_TEXT)

    assert runner.pending_command_count == 1
    runner.wait_for_completion()
