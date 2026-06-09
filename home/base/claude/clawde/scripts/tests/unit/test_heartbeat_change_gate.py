import importlib.util
import pathlib
import sys

HEARTBEAT_DIRECTORY = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "heartbeat"
)


def _load_change_gate_module():
    sys.path.insert(0, str(HEARTBEAT_DIRECTORY))
    module_path = HEARTBEAT_DIRECTORY / "change_gate.py"
    module_spec = importlib.util.spec_from_file_location("change_gate", module_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


change_gate = _load_change_gate_module()


def stub_probe(monkeypatch, return_code, fingerprint):
    monkeypatch.setattr(
        change_gate, "run_probe", lambda probe_command: (return_code, fingerprint)
    )


def test_actionable_fingerprint_fires_once_then_suppresses(monkeypatch, tmp_path):
    state_file = tmp_path / "steward"
    stub_probe(monkeypatch, 0, "diverged-behind-1")
    assert change_gate.gate_fires("probe", state_file) is True
    assert change_gate.gate_fires("probe", state_file) is False
    assert change_gate.gate_fires("probe", state_file) is False


def test_changed_fingerprint_fires_again(monkeypatch, tmp_path):
    state_file = tmp_path / "steward"
    stub_probe(monkeypatch, 0, "diverged-behind-1")
    assert change_gate.gate_fires("probe", state_file) is True
    stub_probe(monkeypatch, 0, "diverged-behind-2")
    assert change_gate.gate_fires("probe", state_file) is True


def test_empty_probe_output_skips_and_forgets(monkeypatch, tmp_path):
    state_file = tmp_path / "steward"
    stub_probe(monkeypatch, 0, "diverged-behind-1")
    assert change_gate.gate_fires("probe", state_file) is True
    stub_probe(monkeypatch, 0, "")
    assert change_gate.gate_fires("probe", state_file) is False
    assert not state_file.exists()
    stub_probe(monkeypatch, 0, "diverged-behind-1")
    assert change_gate.gate_fires("probe", state_file) is True


def test_failed_probe_skips_and_forgets(monkeypatch, tmp_path):
    state_file = tmp_path / "steward"
    stub_probe(monkeypatch, 0, "diverged-behind-1")
    assert change_gate.gate_fires("probe", state_file) is True
    stub_probe(monkeypatch, 3, "")
    assert change_gate.gate_fires("probe", state_file) is False
    assert not state_file.exists()


def test_default_state_file_namespaces_by_label(monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", "/state")
    assert change_gate.default_state_file("betha-pm") == pathlib.Path(
        "/state/clawde-heartbeat-change-gate/betha-pm"
    )


def test_runs_real_probe_command_and_exits_on_change(monkeypatch, tmp_path):
    state_file = tmp_path / "pm"
    assert change_gate.gate_fires("printf actionable", state_file) is True
    assert change_gate.gate_fires("printf actionable", state_file) is False
    assert change_gate.gate_fires("true", state_file) is False
