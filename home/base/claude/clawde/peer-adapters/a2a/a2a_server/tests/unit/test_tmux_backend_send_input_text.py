import subprocess

from a2a_server.backends.tmux_backend import TmuxAttachedAgentBackend


class RecordingTmuxCommandStub:
    def __init__(self) -> None:
        self.invocations: list[list[str]] = []

    def __call__(self, arguments: list[str]) -> subprocess.CompletedProcess:
        self.invocations.append(list(arguments))
        return subprocess.CompletedProcess(
            args=["tmux", *arguments], returncode=0, stdout="", stderr=""
        )


def _build_backend_with_recording_stub() -> tuple[
    TmuxAttachedAgentBackend, RecordingTmuxCommandStub
]:
    backend = TmuxAttachedAgentBackend(
        tmux_session_name="testsession",
        tmux_window_name="testwindow",
        meaningful_line_pattern=None,
    )
    recording_stub = RecordingTmuxCommandStub()
    backend._run_tmux_command = recording_stub
    return backend, recording_stub


class TestSendInputTextUsesLiteralMode:
    def test_send_input_text_passes_literal_flag_for_text_payload(self):
        backend, recording_stub = _build_backend_with_recording_stub()
        backend.send_input_text("hello")
        text_invocation = recording_stub.invocations[0]
        assert "-l" in text_invocation
        flag_index = text_invocation.index("-l")
        assert text_invocation[flag_index + 1] == "hello"

    def test_send_input_text_sends_enter_as_separate_key_press(self):
        backend, recording_stub = _build_backend_with_recording_stub()
        backend.send_input_text("hello")
        enter_invocation = recording_stub.invocations[1]
        assert enter_invocation[-1] == "Enter"
        assert "-l" not in enter_invocation

    def test_send_input_text_with_key_name_input_treats_it_as_literal_text(self):
        backend, recording_stub = _build_backend_with_recording_stub()
        backend.send_input_text("Enter")
        text_invocation = recording_stub.invocations[0]
        assert "-l" in text_invocation
        flag_index = text_invocation.index("-l")
        assert text_invocation[flag_index + 1] == "Enter"

    def test_send_input_text_with_control_sequence_input_treats_it_as_literal_text(
        self,
    ):
        backend, recording_stub = _build_backend_with_recording_stub()
        backend.send_input_text("C-c")
        text_invocation = recording_stub.invocations[0]
        assert "-l" in text_invocation
        flag_index = text_invocation.index("-l")
        assert text_invocation[flag_index + 1] == "C-c"
