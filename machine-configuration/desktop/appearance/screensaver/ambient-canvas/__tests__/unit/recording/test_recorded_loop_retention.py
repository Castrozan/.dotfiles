import pytest

from recording import recorded_loop_retention as retention
from recording.recorded_loop_capture_target import (
    RecordedLoopCaptureTarget,
    compose_recorded_source_identifier,
)
from recording.recorded_segment_store import (
    resolve_recorded_loop_directory,
    store_recorded_segment,
    write_recorded_source_identifier,
)

CURRENT_RENDERING_SOURCE = "/store/web-new theme-background=#181c29"
OLD_RENDERING_SOURCE = "/store/web-old theme-background=#1c251f"


def _record_loop(state_directory, capture_signature, rendering_source):
    loop_directory = resolve_recorded_loop_directory(
        str(state_directory), capture_signature
    )
    store_recorded_segment(loop_directory, capture_signature, "mp4", b"media")
    if rendering_source is not None:
        write_recorded_source_identifier(
            loop_directory,
            compose_recorded_source_identifier(rendering_source, capture_signature),
        )
    return loop_directory


def _capture_target(state_directory, capture_signature):
    return RecordedLoopCaptureTarget(
        loop_directory=resolve_recorded_loop_directory(
            str(state_directory), capture_signature
        ),
        scene_video_directory=str(state_directory / "videos"),
        playback_dwell_override_path=str(state_directory / "playback-dwell-seconds"),
        screen_dimensions=(1280, 720),
        capture_pixel_dimensions=(1920, 1080),
        capture_signature=capture_signature,
    )


@pytest.fixture
def no_record_pass(monkeypatch):
    monkeypatch.setattr(retention, "a_record_pass_is_running", lambda: False)


@pytest.fixture
def state_directory(tmp_path):
    (tmp_path / "videos").mkdir()
    (tmp_path / "videos" / "clip.mp4").write_bytes(b"source")
    (tmp_path / "playback-dwell-seconds").write_text("30\n")
    return tmp_path


def test_a_current_loop_no_longer_keeps_its_source_videos(
    state_directory, no_record_pass
):
    current_loop = _record_loop(state_directory, "1920x1080", CURRENT_RENDERING_SOURCE)
    retention.discard_rendering_leftovers(
        _capture_target(state_directory, "1920x1080"), CURRENT_RENDERING_SOURCE
    )
    assert not (state_directory / "videos").exists()
    assert retention.recorded_loop_is_current(current_loop, CURRENT_RENDERING_SOURCE)
    assert (state_directory / "playback-dwell-seconds").exists()


@pytest.mark.parametrize("sibling_source", [OLD_RENDERING_SOURCE, None])
def test_other_geometries_that_could_only_be_re_encoded_are_deleted(
    state_directory, no_record_pass, sibling_source
):
    current_loop = _record_loop(state_directory, "1920x1080", CURRENT_RENDERING_SOURCE)
    stale_loop = _record_loop(state_directory, "1440x1080", sibling_source)
    discarded = retention.discard_rendering_leftovers(
        _capture_target(state_directory, "1920x1080"), CURRENT_RENDERING_SOURCE
    )
    assert stale_loop in discarded
    assert not (state_directory / "loops" / "1440x1080").exists()
    assert (state_directory / "loops" / "1920x1080" / "loop.source").exists()
    assert current_loop not in discarded


def test_another_geometry_that_is_still_current_survives_for_a_cheap_monitor_swap(
    state_directory, no_record_pass
):
    _record_loop(state_directory, "1920x1080", CURRENT_RENDERING_SOURCE)
    _record_loop(state_directory, "1728x1080", CURRENT_RENDERING_SOURCE)
    retention.discard_rendering_leftovers(
        _capture_target(state_directory, "1920x1080"), CURRENT_RENDERING_SOURCE
    )
    assert (state_directory / "loops" / "1728x1080" / "segments").is_dir()


def test_entries_that_are_not_capture_geometries_are_left_alone(
    state_directory, no_record_pass
):
    _record_loop(state_directory, "1920x1080", CURRENT_RENDERING_SOURCE)
    unrelated_directory = state_directory / "loops" / "notes"
    unrelated_directory.mkdir()
    retention.discard_rendering_leftovers(
        _capture_target(state_directory, "1920x1080"), CURRENT_RENDERING_SOURCE
    )
    assert unrelated_directory.is_dir()


def test_nothing_is_deleted_while_a_record_pass_runs(state_directory, monkeypatch):
    monkeypatch.setattr(retention, "a_record_pass_is_running", lambda: True)
    _record_loop(state_directory, "1920x1080", CURRENT_RENDERING_SOURCE)
    _record_loop(state_directory, "1440x1080", None)
    assert (
        retention.discard_rendering_leftovers(
            _capture_target(state_directory, "1920x1080"), CURRENT_RENDERING_SOURCE
        )
        == []
    )
    assert (state_directory / "videos" / "clip.mp4").exists()
    assert (state_directory / "loops" / "1440x1080").is_dir()


def test_a_state_directory_without_leftovers_is_a_no_op(tmp_path, no_record_pass):
    assert (
        retention.discard_rendering_leftovers(
            _capture_target(tmp_path, "1920x1080"), CURRENT_RENDERING_SOURCE
        )
        == []
    )
