import json
import subprocess

from a2a_server.backends.herdr_backend import HerdrAttachedAgentBackend


class RecordingHerdrCommandStub:
    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.invocations: list[list[str]] = []
        self._returncode = returncode
        self._stdout = stdout

    def __call__(self, arguments: list[str]) -> subprocess.CompletedProcess:
        self.invocations.append(list(arguments))
        return subprocess.CompletedProcess(
            args=["herdr", *arguments],
            returncode=self._returncode,
            stdout=self._stdout,
            stderr="",
        )


def _build_backend_with_stub(
    returncode: int = 0, stdout: str = ""
) -> tuple[HerdrAttachedAgentBackend, RecordingHerdrCommandStub]:
    backend = HerdrAttachedAgentBackend("wP:pT", meaningful_line_pattern=None)
    recording_stub = RecordingHerdrCommandStub(returncode=returncode, stdout=stdout)
    backend._run_herdr_command = recording_stub
    return backend, recording_stub


def _pane_get_payload_with_agent(agent_value) -> str:
    return json.dumps({"result": {"pane": {"pane_id": "wP:pT", "agent": agent_value}}})


class TestCancelGracefullyInterruptsWithControlC:
    def test_cancel_gracefully_sends_control_c_to_target_pane(self):
        backend, recording_stub = _build_backend_with_stub()
        backend.cancel_gracefully()
        assert recording_stub.invocations == [["pane", "send-keys", "wP:pT", "C-c"]]


class TestStopClosesTargetPane:
    def test_stop_closes_target_pane(self):
        backend, recording_stub = _build_backend_with_stub()
        backend.stop()
        assert recording_stub.invocations == [["pane", "close", "wP:pT"]]


class TestTargetHerdrPaneExistsUsesPaneGetReturnCode:
    def test_existence_query_uses_pane_get(self):
        backend, recording_stub = _build_backend_with_stub(returncode=0)
        backend._target_herdr_pane_exists()
        assert recording_stub.invocations == [["pane", "get", "wP:pT"]]

    def test_pane_exists_when_pane_get_succeeds(self):
        backend, _ = _build_backend_with_stub(returncode=0)
        assert backend._target_herdr_pane_exists() is True

    def test_pane_absent_when_pane_get_fails(self):
        backend, _ = _build_backend_with_stub(returncode=1)
        assert backend._target_herdr_pane_exists() is False


class TestCapturePaneTextReadsRecentUnwrapped:
    def test_capture_reads_recent_unwrapped_two_hundred_lines(self):
        backend, recording_stub = _build_backend_with_stub(
            returncode=0, stdout="captured"
        )
        backend._capture_pane_text()
        assert recording_stub.invocations == [
            [
                "pane",
                "read",
                "wP:pT",
                "--source",
                "recent-unwrapped",
                "--lines",
                "200",
            ]
        ]

    def test_capture_returns_stdout_on_success(self):
        backend, _ = _build_backend_with_stub(returncode=0, stdout="captured text")
        assert backend._capture_pane_text() == "captured text"

    def test_capture_returns_empty_string_when_read_fails(self):
        backend, _ = _build_backend_with_stub(returncode=1, stdout="partial")
        assert backend._capture_pane_text() == ""


class TestLiveAgentDetectionUsesPaneGetAgentField:
    def test_liveness_query_uses_pane_get(self):
        backend, recording_stub = _build_backend_with_stub(
            returncode=0, stdout=_pane_get_payload_with_agent("claude")
        )
        backend._target_pane_hosts_live_agent()
        assert recording_stub.invocations == [["pane", "get", "wP:pT"]]

    def test_alive_when_pane_reports_an_agent(self):
        backend, _ = _build_backend_with_stub(
            returncode=0, stdout=_pane_get_payload_with_agent("claude")
        )
        assert backend._target_pane_hosts_live_agent() is True

    def test_not_alive_when_pane_agent_is_null(self):
        backend, _ = _build_backend_with_stub(
            returncode=0, stdout=_pane_get_payload_with_agent(None)
        )
        assert backend._target_pane_hosts_live_agent() is False

    def test_not_alive_when_pane_get_fails(self):
        backend, _ = _build_backend_with_stub(
            returncode=1, stdout=_pane_get_payload_with_agent("claude")
        )
        assert backend._target_pane_hosts_live_agent() is False

    def test_not_alive_when_pane_get_output_is_not_json(self):
        backend, _ = _build_backend_with_stub(returncode=0, stdout="not json at all")
        assert backend._target_pane_hosts_live_agent() is False
