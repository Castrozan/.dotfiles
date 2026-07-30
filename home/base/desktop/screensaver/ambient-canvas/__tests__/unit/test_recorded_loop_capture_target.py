import ensure_ambient_canvas_screensaver as ensure
import recorded_loop_capture_plan as capture_plan
import recorded_loop_capture_target as capture_target
import recorded_segment_store as store

WEB_SOURCE_IDENTIFIER = "/store/web-abc"
LAPTOP_SCREEN_DIMENSIONS = (1470, 956)
EXTERNAL_SCREEN_DIMENSIONS = (1920, 1080)
LAPTOP_CAPTURE_SIGNATURE = "1660x1080"
EXTERNAL_CAPTURE_SIGNATURE = "1920x1080"


def _record_loop_for(state_directory, capture_signature, segment_fingerprint):
    loop_directory = store.resolve_recorded_loop_directory(
        state_directory, capture_signature
    )
    store.store_recorded_segment(loop_directory, segment_fingerprint, "mp4", b"media")
    recorded_manifest = store.build_recorded_segment_manifest(
        [
            {
                "fingerprint": segment_fingerprint,
                "extension": "mp4",
                "durationSeconds": 30,
            }
        ]
    )
    store.write_recorded_segment_manifest(loop_directory, recorded_manifest)
    store.prune_recorded_segments_outside_manifest(loop_directory, recorded_manifest)
    store.write_recorded_source_identifier(
        loop_directory,
        capture_target.compose_recorded_source_identifier(
            WEB_SOURCE_IDENTIFIER, capture_signature
        ),
    )
    return loop_directory


def test_capture_signature_names_the_recorded_pixel_size():
    assert capture_plan.format_capture_signature((1660, 1080)) == "1660x1080"


def test_every_capture_geometry_owns_its_own_loop_directory():
    assert (
        store.resolve_recorded_loop_directory("/state", LAPTOP_CAPTURE_SIGNATURE)
        == "/state/loops/1660x1080"
    )
    assert (
        store.resolve_recorded_loop_directory("/state", EXTERNAL_CAPTURE_SIGNATURE)
        == "/state/loops/1920x1080"
    )


def test_the_capture_target_follows_the_main_display(monkeypatch):
    monkeypatch.setattr(
        capture_target, "read_screen_dimensions", lambda: LAPTOP_SCREEN_DIMENSIONS
    )
    resolved = capture_target.resolve_recorded_loop_capture_target("/state")
    assert resolved.screen_dimensions == LAPTOP_SCREEN_DIMENSIONS
    assert resolved.capture_pixel_dimensions == (1660, 1080)
    assert resolved.capture_signature == LAPTOP_CAPTURE_SIGNATURE
    assert resolved.loop_directory == "/state/loops/1660x1080"


def test_the_capture_target_reads_the_display_once_so_the_cache_key_cannot_drift(
    monkeypatch,
):
    observed_reads = []

    def counted_read():
        observed_reads.append("read")
        return LAPTOP_SCREEN_DIMENSIONS

    monkeypatch.setattr(capture_target, "read_screen_dimensions", counted_read)
    capture_target.resolve_recorded_loop_capture_target("/state")
    assert observed_reads == ["read"]


def test_scene_videos_are_shared_by_every_capture_geometry(monkeypatch):
    monkeypatch.setattr(
        capture_target, "read_screen_dimensions", lambda: LAPTOP_SCREEN_DIMENSIONS
    )
    laptop = capture_target.resolve_recorded_loop_capture_target("/state")
    monkeypatch.setattr(
        capture_target, "read_screen_dimensions", lambda: EXTERNAL_SCREEN_DIMENSIONS
    )
    external = capture_target.resolve_recorded_loop_capture_target("/state")
    assert laptop.scene_video_directory == "/state/videos"
    assert external.scene_video_directory == "/state/videos"
    assert laptop.loop_directory != external.loop_directory


def test_capture_dimensions_join_the_freshness_identifier():
    assert (
        capture_target.compose_recorded_source_identifier(
            WEB_SOURCE_IDENTIFIER, LAPTOP_CAPTURE_SIGNATURE
        )
        == "/store/web-abc capture=1660x1080"
    )


def test_switching_displays_keeps_both_recorded_loops_cached(tmp_path):
    state_directory = str(tmp_path)
    laptop_loop = _record_loop_for(
        state_directory, LAPTOP_CAPTURE_SIGNATURE, "laptopsegment"
    )
    external_loop = _record_loop_for(
        state_directory, EXTERNAL_CAPTURE_SIGNATURE, "externalsegment"
    )
    assert ensure.recorded_loop_is_fresh(
        laptop_loop,
        capture_target.compose_recorded_source_identifier(
            WEB_SOURCE_IDENTIFIER, LAPTOP_CAPTURE_SIGNATURE
        ),
    )
    assert ensure.recorded_loop_is_fresh(
        external_loop,
        capture_target.compose_recorded_source_identifier(
            WEB_SOURCE_IDENTIFIER, EXTERNAL_CAPTURE_SIGNATURE
        ),
    )


def test_recording_one_display_never_prunes_another_displays_segments(tmp_path):
    state_directory = str(tmp_path)
    laptop_loop = _record_loop_for(
        state_directory, LAPTOP_CAPTURE_SIGNATURE, "laptopsegment"
    )
    _record_loop_for(state_directory, EXTERNAL_CAPTURE_SIGNATURE, "externalsegment")
    assert store.list_recorded_segment_fingerprints(laptop_loop) == ["laptopsegment"]
