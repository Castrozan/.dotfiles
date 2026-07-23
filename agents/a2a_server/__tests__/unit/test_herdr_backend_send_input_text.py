import subprocess

from a2a_server.backends.herdr_backend import HerdrAttachedAgentBackend


class RecordingHerdrCommandStub:
    def __init__(self) -> None:
        self.invocations: list[list[str]] = []

    def __call__(self, arguments: list[str]) -> subprocess.CompletedProcess:
        self.invocations.append(list(arguments))
        return subprocess.CompletedProcess(
            args=["herdr", *arguments], returncode=0, stdout="", stderr=""
        )


def _build_backend_with_recording_stub() -> tuple[
    HerdrAttachedAgentBackend, RecordingHerdrCommandStub
]:
    backend = HerdrAttachedAgentBackend(
        herdr_pane_id="wP:pT",
        meaningful_line_pattern=None,
    )
    recording_stub = RecordingHerdrCommandStub()
    backend._run_herdr_command = recording_stub
    return backend, recording_stub


class TestSendInputTextWritesLiteralPayloadThenEnter:
    def test_send_input_text_writes_payload_as_send_text(self):
        backend, recording_stub = _build_backend_with_recording_stub()
        backend.send_input_text("hello")
        text_invocation = recording_stub.invocations[0]
        assert text_invocation == ["pane", "send-text", "wP:pT", "hello"]

    def test_send_input_text_sends_enter_as_separate_key_press(self):
        backend, recording_stub = _build_backend_with_recording_stub()
        backend.send_input_text("hello")
        enter_invocation = recording_stub.invocations[1]
        assert enter_invocation == ["pane", "send-keys", "wP:pT", "Enter"]

    def test_send_input_text_with_key_name_input_treats_it_as_literal_text(self):
        backend, recording_stub = _build_backend_with_recording_stub()
        backend.send_input_text("Enter")
        text_invocation = recording_stub.invocations[0]
        assert text_invocation == ["pane", "send-text", "wP:pT", "Enter"]

    def test_send_input_text_with_control_sequence_input_treats_it_as_literal_text(
        self,
    ):
        backend, recording_stub = _build_backend_with_recording_stub()
        backend.send_input_text("C-c")
        text_invocation = recording_stub.invocations[0]
        assert text_invocation == ["pane", "send-text", "wP:pT", "C-c"]
