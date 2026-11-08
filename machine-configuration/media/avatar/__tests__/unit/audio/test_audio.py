import pytest

from pulse_audio_fake import Pulse, audio


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
    assert len(state["modules"]) == 7
    assert not state.get("microphone")
    for name in audio.CHANNELS.values():
        assert ("set-sink-mute", name, "1") in pulse.calls
        assert ("set-sink-volume", name, "100%") in pulse.calls
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


def test_opening_a_meeting_attaches_the_default_microphone_and_unmutes_both_voices(
    tmp_path, pulse
):
    path = tmp_path / "state.json"
    state = {"modules": []}
    audio.start(path, state)
    audio.open_meeting_inputs(path, state)
    audio.open_meeting_inputs(path, state)
    assert state["microphone"]["source"] == "synthetic-human.monitor"
    unmuted = [call[1] for call in pulse.calls if call[0::2] == ("set-sink-mute", "0")]
    assert unmuted == ["AvatarMic", "AvatarHuman"] * 2


def test_opening_a_meeting_refuses_a_default_source_that_would_feed_itself(
    tmp_path, pulse
):
    path = tmp_path / "state.json"
    state = {"modules": []}
    audio.start(path, state)
    pulse.default_source = "AvatarMicrophone"
    with pytest.raises(ValueError, match="cannot feed"):
        audio.open_meeting_inputs(path, state)


def test_attach_requires_existing_non_feedback_source(tmp_path, pulse):
    path = tmp_path / "state.json"
    state = {"modules": []}
    audio.start(path, state)
    with pytest.raises(ValueError, match="cannot feed"):
        audio.connect_microphone(path, state, "AvatarMicrophone")
    with pytest.raises(ValueError, match="does not exist"):
        audio.connect_microphone(path, state, "missing")
    audio.connect_microphone(path, state, "synthetic-human.monitor")
    assert state["microphone"]["source"] == "synthetic-human.monitor"
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
