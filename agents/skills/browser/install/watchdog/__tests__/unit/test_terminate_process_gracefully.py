class RecordingFakeProcess:
    def __init__(self, wait_side_effect=None, terminate_side_effect=None):
        self.wait_side_effect = wait_side_effect
        self.terminate_side_effect = terminate_side_effect
        self.terminate_was_called = False
        self.kill_was_called = False
        self.wait_timeout_received = None

    def terminate(self):
        self.terminate_was_called = True
        if self.terminate_side_effect is not None:
            raise self.terminate_side_effect

    def wait(self, timeout=None):
        self.wait_timeout_received = timeout
        if self.wait_side_effect is not None:
            raise self.wait_side_effect

    def kill(self):
        self.kill_was_called = True


def test_escalates_to_kill_when_wait_times_out(watchdog_module):
    process = RecordingFakeProcess(
        wait_side_effect=watchdog_module.psutil.TimeoutExpired()
    )
    watchdog_module.terminate_process_gracefully(process, sigterm_grace_seconds=5.0)
    assert process.terminate_was_called
    assert process.wait_timeout_received == 5.0
    assert process.kill_was_called


def test_does_not_kill_when_terminate_succeeds_within_grace(watchdog_module):
    process = RecordingFakeProcess()
    watchdog_module.terminate_process_gracefully(process, sigterm_grace_seconds=5.0)
    assert process.terminate_was_called
    assert not process.kill_was_called


def test_swallows_disappeared_process_without_killing(watchdog_module):
    process = RecordingFakeProcess(
        terminate_side_effect=watchdog_module.psutil.NoSuchProcess()
    )
    watchdog_module.terminate_process_gracefully(process, sigterm_grace_seconds=5.0)
    assert process.terminate_was_called
    assert not process.kill_was_called


def test_swallows_disappearance_during_kill_escalation(watchdog_module):
    process = RecordingFakeProcess(
        wait_side_effect=watchdog_module.psutil.TimeoutExpired()
    )

    def kill_raising_no_such_process():
        process.kill_was_called = True
        raise watchdog_module.psutil.NoSuchProcess()

    process.kill = kill_raising_no_such_process
    watchdog_module.terminate_process_gracefully(process, sigterm_grace_seconds=5.0)
    assert process.kill_was_called
