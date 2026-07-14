import importlib.util
import pathlib

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "precompute_loop.py"
)


def _load_precompute_loop_module():
    module_spec = importlib.util.spec_from_file_location("precompute_loop", SCRIPT_PATH)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


precompute_loop = _load_precompute_loop_module()


def test_extract_command_strips_leading_separator():
    assert precompute_loop.extract_command(["--", "cmatrix", "-b"]) == ["cmatrix", "-b"]


def test_extract_command_passes_through_without_separator():
    assert precompute_loop.extract_command(["cmatrix", "-b"]) == ["cmatrix", "-b"]


def test_cast_path_varies_with_size_command_and_seconds():
    first = precompute_loop.resolve_cast_path(["cmatrix"], 60.0, 80, 24)
    wider = precompute_loop.resolve_cast_path(["cmatrix"], 60.0, 200, 50)
    other = precompute_loop.resolve_cast_path(["cbonsai"], 60.0, 80, 24)
    shorter = precompute_loop.resolve_cast_path(["cmatrix"], 30.0, 80, 24)
    assert first != wider
    assert first != other
    assert first != shorter
    assert first.name == "cast.bin"


def test_terminate_child_escalates_to_sigkill_when_sigterm_ignored(monkeypatch):
    signals_sent = []
    monkeypatch.setattr(
        precompute_loop.os, "kill", lambda pid, number: signals_sent.append(number)
    )
    monkeypatch.setattr(precompute_loop.os, "waitpid", lambda pid, flags: (0, 0))
    monkeypatch.setattr(precompute_loop.os, "close", lambda fd: None)
    ticks = iter([0.0, 0.1, 0.6, 0.6, 0.7, 1.2])
    monkeypatch.setattr(precompute_loop.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(precompute_loop.time, "sleep", lambda seconds: None)
    precompute_loop.terminate_child(4242, 9)
    assert signals_sent == [
        precompute_loop.signal.SIGTERM,
        precompute_loop.signal.SIGKILL,
    ]


def test_terminate_child_stops_at_sigterm_when_child_exits(monkeypatch):
    signals_sent = []
    monkeypatch.setattr(
        precompute_loop.os, "kill", lambda pid, number: signals_sent.append(number)
    )
    monkeypatch.setattr(precompute_loop.os, "waitpid", lambda pid, flags: (pid, 0))
    monkeypatch.setattr(precompute_loop.os, "close", lambda fd: None)
    ticks = iter([0.0, 0.1])
    monkeypatch.setattr(precompute_loop.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(precompute_loop.time, "sleep", lambda seconds: None)
    precompute_loop.terminate_child(4242, 9)
    assert signals_sent == [precompute_loop.signal.SIGTERM]


def test_cast_file_round_trips_chunks(tmp_path):
    cast_path = tmp_path / "cast.bin"
    chunks = [(0.0, b"\033[Hfirst"), (0.033, b"\033[2;1Hsecond"), (0.5, b"third")]
    precompute_loop.write_cast_file(cast_path, chunks)
    assert precompute_loop.load_cast_file(cast_path) == chunks


def test_load_cast_file_rejects_foreign_content(tmp_path):
    cast_path = tmp_path / "cast.bin"
    cast_path.write_bytes(b"not a cast file")
    assert precompute_loop.load_cast_file(cast_path) is None
