import array
import wave

import pytest
from shorts_timing import audible_end, validate_endings


def narration(tmp_path, speech=2, silence=0):
    path = tmp_path / "voice.wav"
    samples = array.array("h", [2000, -2000] * int(speech * 4000))
    samples.extend([0] * int(silence * 8000))
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        output.writeframes(samples.tobytes())
    return path


def test_padded_audio_container_cannot_hide_several_second_tail(tmp_path):
    path = narration(tmp_path, speech=2, silence=3)
    assert audible_end(path) == pytest.approx(2)
    stream = {"duration": "5", "start_time": "0"}
    with pytest.raises(ValueError, match="trails edited narration by 3.000s"):
        validate_endings(5, stream, stream, path, 0)


@pytest.mark.parametrize("tail", [0, 0.5, 0.99, 1.0])
def test_short_breath_after_complete_narration_is_accepted(tmp_path, tail):
    path = narration(tmp_path)
    stream = {"duration": str(2 + tail)}
    result = validate_endings(2 + tail, stream, stream, path, 0)
    assert result["tail_seconds"] == pytest.approx(tail)


def test_final_video_cannot_cut_off_the_spoken_ending(tmp_path):
    path = narration(tmp_path)
    with pytest.raises(ValueError, match="preserve the full speech"):
        validate_endings(1.8, {"duration": 1.8}, {"duration": 1.8}, path, 0)


def test_delayed_narration_uses_actual_timeline_offset(tmp_path):
    path = narration(tmp_path)
    result = validate_endings(3.5, {"duration": 3.5}, {"duration": 3.5}, path, 1)
    assert result["tail_seconds"] == 0.5


def test_audio_ending_before_picture_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="within 100ms"):
        validate_endings(5, {"duration": 5}, {"duration": 2}, narration(tmp_path), 0)


@pytest.mark.parametrize("offset", [-1, float("nan"), float("inf")])
def test_invalid_offsets_cannot_bypass_tail_limit(tmp_path, offset):
    with pytest.raises(ValueError, match="finite nonnegative"):
        validate_endings(
            2, {"duration": 2}, {"duration": 2}, narration(tmp_path), offset
        )


def test_empty_voice_track_is_not_accepted(tmp_path):
    with pytest.raises(ValueError, match="no measurable"):
        audible_end(narration(tmp_path, speech=0, silence=2))
