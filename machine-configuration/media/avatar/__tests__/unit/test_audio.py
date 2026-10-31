import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "avatar_audio", Path(__file__).resolve().parents[2] / "scripts/audio.py"
)
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)


class Pulse:
    def __init__(self):
        self.modules = [{"index": 1, "name": "unrelated", "argument": "keep"}]
        self.sinks = []
        self.sources = [{"name": "synthetic-human.monitor"}]
        self.calls = []
        self.next_identifier = 100
        self.failure = None

    def items(self, kind):
        return getattr(self, kind)

    def call(self, *arguments):
        self.calls.append(arguments)
        if self.failure == arguments[0]:
            raise RuntimeError("injected Pulse failure")
        if arguments[0] == "load-module":
            identifier = self.next_identifier
            self.next_identifier += 1
            self.modules.append(
                {
                    "index": identifier,
                    "name": arguments[1],
                    "argument": " ".join(arguments[2:]),
                }
            )
            for argument in arguments[2:]:
                if argument.startswith("sink_name="):
                    self.sinks.append(
                        {"name": argument.split("=", 1)[1], "owner": identifier}
                    )
                if argument.startswith("source_name="):
                    self.sources.append(
                        {"name": argument.split("=", 1)[1], "owner": identifier}
                    )
            return str(identifier)
        if arguments[0] == "unload-module":
            identifier = int(arguments[1])
            self.modules = [
                item for item in self.modules if item["index"] != identifier
            ]
            self.sinks = [
                item for item in self.sinks if item.get("owner") != identifier
            ]
            self.sources = [
                item for item in self.sources if item.get("owner") != identifier
            ]
        return ""


@pytest.fixture
def pulse(monkeypatch):
    backend = Pulse()
    monkeypatch.setattr(audio.pulse_audio, "run", backend.call)
    monkeypatch.setattr(audio.pulse_audio, "items", backend.items)
    return backend


def test_start_is_muted_isolated_and_repeatable(tmp_path, pulse):
    path = tmp_path / "state.json"
    state = {"modules": []}
    audio.start(path, state)
    assert len(state["modules"]) == 6
    assert not state.get("microphone")
    for name in audio.CHANNELS.values():
        assert ("set-sink-mute", name, "1") in pulse.calls
        assert ("set-sink-volume", name, "50%") in pulse.calls
    assert all("default" not in " ".join(call) for call in pulse.calls)
    assert (
        sum(
            call[1] == "module-loopback"
            for call in pulse.calls
            if call[0] == "load-module"
        )
        == 2
    )
    before = list(pulse.calls)
    audio.start(path, state)
    assert pulse.calls == before
    audio.stop(path, state)
    audio.stop(path, state)
    assert pulse.modules == [{"index": 1, "name": "unrelated", "argument": "keep"}]
    assert not path.exists()


def test_partial_start_rolls_back_owned_modules(tmp_path, pulse):
    path = tmp_path / "state.json"
    state = {"modules": []}
    pulse.failure = "set-sink-volume"
    with pytest.raises(RuntimeError):
        audio.start(path, state)
    assert pulse.modules == [{"index": 1, "name": "unrelated", "argument": "keep"}]
    assert not path.exists()


def test_stop_does_not_unload_reused_module_identifier(tmp_path, pulse):
    path = tmp_path / "state.json"
    state = {"modules": []}
    audio.start(path, state)
    replaced = pulse.modules[-1]
    replaced["argument"] = "now_owned_by_someone_else"
    audio.stop(path, state)
    assert replaced in pulse.modules


def test_start_refuses_unowned_name_collision(tmp_path, pulse):
    pulse.sinks.append({"name": "AvatarMic"})
    with pytest.raises(ValueError, match="Refusing to adopt"):
        audio.start(tmp_path / "state.json", {"modules": []})
    assert not pulse.calls


def test_attach_requires_existing_non_feedback_source(tmp_path, pulse):
    path = tmp_path / "state.json"
    state = {"modules": []}
    audio.start(path, state)
    with pytest.raises(ValueError, match="cannot feed"):
        audio.connect_microphone(path, state, "AvatarMicrophone")
    with pytest.raises(ValueError, match="does not exist"):
        audio.connect_microphone(path, state, "missing")
    audio.connect_microphone(path, state, "synthetic-human.monitor")
    assert state["microphone"] == "synthetic-human.monitor"
    call = next(
        call for call in pulse.calls if "source=synthetic-human.monitor" in call
    )
    assert "sink=AvatarHuman" in call
    assert "source_dont_move=true" in call
    assert "sink_dont_move=true" in call
    with pytest.raises(ValueError, match="already attached"):
        audio.connect_microphone(path, state, "synthetic-human.monitor")


def test_parse_modules_handles_multiline_native_modules():
    output = "1\tlibpipewire-module-rt\t{\n    rt.prio = 88\n}\t\n536870916\tmodule-null-sink\tsink_name=AvatarMic rate=48000\t\n"
    assert audio.pulse_audio.parse_modules(output)[-1] == {
        "index": 536870916,
        "name": "module-null-sink",
        "argument": "sink_name=AvatarMic rate=48000",
    }


def test_active_agent_playback_prevents_fallback_during_stop(
    tmp_path, pulse, monkeypatch
):
    path = tmp_path / "state.json"
    state = {"modules": []}
    audio.start(path, state)
    modules = list(pulse.modules)
    monkeypatch.setattr(audio.pulse_audio, "active_playbacks", lambda _: ["app-stream"])
    with pytest.raises(ValueError, match="inputs remain muted"):
        audio.stop(path, state)
    assert pulse.modules == modules
    assert path.exists()
    for name in audio.CHANNELS.values():
        assert ("set-sink-mute", name, "1") in pulse.calls
    monkeypatch.setattr(audio.pulse_audio, "active_playbacks", lambda _: [])
    audio.stop(path, state)
    assert not path.exists()
