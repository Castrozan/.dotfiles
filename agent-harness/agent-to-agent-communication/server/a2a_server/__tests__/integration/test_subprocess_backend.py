import time

from a2a_server.backends.subprocess_backend import SubprocessAgentBackend


def _wait_until_observation_contains(
    backend, expected_substring, total_wait_budget_seconds=5.0
):
    accumulated_output = ""
    deadline_epoch_seconds = time.time() + total_wait_budget_seconds
    while time.time() < deadline_epoch_seconds:
        accumulated_output += backend.observe().raw_output_since_last_call
        if expected_substring in accumulated_output:
            return accumulated_output
        time.sleep(0.05)
    return accumulated_output


class TestSubprocessAgentBackend:
    def test_observes_output_from_a_simple_echo_subprocess(self):
        backend = SubprocessAgentBackend(
            command_argv=["bash", "-c", "echo hello-from-subprocess"]
        )
        try:
            backend.start()
            captured = _wait_until_observation_contains(
                backend, "hello-from-subprocess"
            )
            assert "hello-from-subprocess" in captured
        finally:
            backend.stop()

    def test_observe_reports_not_alive_after_subprocess_exits(self):
        backend = SubprocessAgentBackend(command_argv=["bash", "-c", "true"])
        try:
            backend.start()
            time.sleep(0.3)
            for _ in range(20):
                observation = backend.observe()
                if not observation.is_alive:
                    break
                time.sleep(0.05)
            assert not observation.is_alive
        finally:
            backend.stop()

    def test_send_input_text_is_visible_in_observation(self):
        backend = SubprocessAgentBackend(command_argv=["cat"])
        try:
            backend.start()
            backend.send_input_text("echoed-line\n")
            captured = _wait_until_observation_contains(backend, "echoed-line")
            assert "echoed-line" in captured
        finally:
            backend.stop()
