import json
import stat
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import listen_cli
import listener_session
import speaker_identity
import transcript_echo
import transcript_log


def test_a_listener_without_identity_names_no_one_and_keeps_no_embedding():
    identifier = speaker_identity.configured_identifier(False)

    assert identifier.identify(b"\0\0") == (None, None)


def test_a_phrase_heard_by_another_source_within_seconds_is_an_echo():
    echoes = transcript_echo.EchoFilter()
    assert not echoes.is_echo("meeting", "Let's start the review, everyone.", 100)
    assert echoes.is_echo("human", "lets start the review everyone", 103)


def test_a_longer_echo_containing_the_first_phrase_is_dropped():
    echoes = transcript_echo.EchoFilter()
    assert not echoes.is_echo("human", "start the review", 100)
    assert echoes.is_echo("meeting", "okay so let us start the review now", 101)


def test_a_short_phrase_inside_another_is_not_an_echo():
    echoes = transcript_echo.EchoFilter()
    assert not echoes.is_echo("human", "yes sure", 100)
    assert not echoes.is_echo("meeting", "yes sure that works for the whole team", 101)


def test_the_same_source_repeating_itself_is_kept():
    echoes = transcript_echo.EchoFilter()
    assert not echoes.is_echo("human", "no no no", 100)
    assert not echoes.is_echo("human", "no no no", 101)


def test_an_old_phrase_is_not_an_echo():
    echoes = transcript_echo.EchoFilter()
    assert not echoes.is_echo("meeting", "see you tomorrow morning", 100)
    assert not echoes.is_echo("human", "see you tomorrow morning", 116)


def test_cosine_similarity_compares_direction_only():
    assert speaker_identity.cosine_similarity([1, 0], [3, 0]) == pytest.approx(1)
    assert speaker_identity.cosine_similarity([1, 0], [0, 2]) == pytest.approx(0)
    assert speaker_identity.cosine_similarity([1, 0], [1, 0, 0]) == 0
    assert speaker_identity.cosine_similarity([0, 0], [1, 0]) == 0


def test_profiles_are_private_and_match_above_the_threshold(tmp_path):
    profiles = speaker_identity.VoiceProfiles(tmp_path / "voices")
    profiles.save("ana", [1, 0], 3)
    profiles.save("bia", [0, 1], 3)
    assert stat.S_IMODE((tmp_path / "voices").stat().st_mode) == 0o700
    assert stat.S_IMODE((tmp_path / "voices" / "ana.json").stat().st_mode) == 0o600
    assert profiles.best_match([0.9, 0.1]) == "ana"
    assert profiles.best_match([0.1, 0.9]) == "bia"
    assert profiles.best_match([-1, -1]) is None
    assert profiles.names() == ["ana", "bia"]


def write_embeddings(path, count):
    for sequence in range(1, count + 1):
        speaker_identity.append_embedding(path, sequence, [1.0, 0.1 * sequence])


def test_enrolling_averages_the_chosen_sequences(tmp_path):
    embeddings = tmp_path / "embeddings.jsonl"
    write_embeddings(embeddings, 5)
    profiles = speaker_identity.VoiceProfiles(tmp_path / "voices")
    assert speaker_identity.enroll(profiles, embeddings, "ana", 2, 4) == 3
    assert profiles.load("ana")["samples"] == 3
    assert stat.S_IMODE(embeddings.stat().st_mode) == 0o600


def test_enrolling_needs_three_embeddings(tmp_path):
    embeddings = tmp_path / "embeddings.jsonl"
    write_embeddings(embeddings, 5)
    profiles = speaker_identity.VoiceProfiles(tmp_path / "voices")
    with pytest.raises(ValueError, match="at least 3"):
        speaker_identity.enroll(profiles, embeddings, "ana", 1, 2)
    assert profiles.names() == []


@pytest.mark.parametrize("name", ["", "../ana", "a b", "ana.json", "ana\n", "ânia"])
def test_voice_names_outside_the_safe_alphabet_are_refused(tmp_path, name):
    embeddings = tmp_path / "embeddings.jsonl"
    write_embeddings(embeddings, 5)
    profiles = speaker_identity.VoiceProfiles(tmp_path / "voices")
    with pytest.raises(ValueError):
        speaker_identity.enroll(profiles, embeddings, name, 1, 5)
    with pytest.raises(ValueError):
        profiles.forget(name)


def test_forgetting_deletes_only_the_named_profile(tmp_path):
    profiles = speaker_identity.VoiceProfiles(tmp_path)
    profiles.save("ana", [1, 0], 3)
    profiles.save("bia", [0, 1], 3)
    profiles.forget("ana")
    assert profiles.names() == ["bia"]
    with pytest.raises(ValueError):
        profiles.forget("ana")


def test_a_segment_is_named_by_its_closest_enrolled_voice(tmp_path):
    profiles = speaker_identity.VoiceProfiles(tmp_path)
    profiles.save("ana", [1, 0], 3)
    identifier = speaker_identity.SpeakerIdentifier(
        "model.onnx", profiles, lambda _: lambda segment: [1.0, 0.0]
    )
    assert identifier.identify(b"audio") == ("ana", [1.0, 0.0])


def test_a_model_that_fails_to_load_leaves_speakers_unknown(tmp_path, capsys):
    loader = Mock(side_effect=RuntimeError("no model"))
    identifier = speaker_identity.SpeakerIdentifier(
        "model.onnx", speaker_identity.VoiceProfiles(tmp_path), loader
    )
    assert identifier.identify(b"audio") == (None, None)
    assert identifier.identify(b"audio") == (None, None)
    loader.assert_called_once()
    assert "no model" in capsys.readouterr().err


def test_a_missing_model_path_leaves_speakers_unknown(tmp_path, capsys):
    identifier = speaker_identity.SpeakerIdentifier(
        None, speaker_identity.VoiceProfiles(tmp_path), Mock()
    )
    assert identifier.identify(b"audio") == (None, None)
    assert "AVATAR_SPEAKER_MODEL" in capsys.readouterr().err


def test_speakers_are_recorded_without_embeddings_in_the_transcript(tmp_path):
    path = tmp_path / "transcript.jsonl"
    transcript_log.append(path, "meeting", "hello", "ana")
    transcript_log.append(path, "human", "hi")
    entries = transcript_log.read_since(path, 0)
    assert [entry["speaker"] for entry in entries] == ["ana", None]
    assert all("embedding" not in entry for entry in entries)


def test_starting_again_removes_the_previous_embeddings(tmp_path, monkeypatch):
    monkeypatch.setattr(listener_session, "systemctl", Mock())
    (tmp_path / "embeddings.jsonl").write_text("{}")
    listener_session.begin_listening(
        tmp_path, listener_session.ListenerPurpose.MEETING, {"meeting": "any"}
    )
    assert not (tmp_path / "embeddings.jsonl").exists()


def test_enroll_command_reports_the_profile(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    write_embeddings(tmp_path / "embeddings.jsonl", 3)
    arguments = SimpleNamespace(name="ana", first=1, last=3)
    listen_cli.enroll(arguments, tmp_path)
    assert json.loads(capsys.readouterr().out) == {"enrolled": "ana", "samples": 3}
    listen_cli.voices(arguments, tmp_path)
    assert json.loads(capsys.readouterr().out) == {"voices": ["ana"]}
    listen_cli.forget(arguments, tmp_path)
    assert json.loads(capsys.readouterr().out) == {"forgotten": "ana"}
