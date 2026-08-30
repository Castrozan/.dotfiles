import json
import pathlib
import subprocess

import recorded_segment_manifest as segment_manifest

AMBIENT_CANVAS_DIRECTORY = pathlib.Path(__file__).resolve().parents[2]
RECORDING_PLAN_SOURCE = (
    AMBIENT_CANVAS_DIRECTORY / "web" / "record" / "ambient-canvas-recording-plan.js"
)
RECORDING_FINGERPRINT_SOURCE = (
    AMBIENT_CANVAS_DIRECTORY
    / "web"
    / "record"
    / "ambient-canvas-recording-fingerprint.js"
)
PLAYLIST_SOURCE = (AMBIENT_CANVAS_DIRECTORY / "web" / "panes.js").read_text()
DOCUMENT_SOURCE = (AMBIENT_CANVAS_DIRECTORY / "web" / "index.html").read_text()
RECORDER_SOURCE = (AMBIENT_CANVAS_DIRECTORY / "web" / "recorder.js").read_text()
BAD_APPLE_SOURCE = (
    AMBIENT_CANVAS_DIRECTORY / "web" / "scenes" / "bad-apple" / "bad_apple_scene.js"
).read_text()


def resolve_recording_ranges(recording_source, chunk_duration_seconds):
    evaluation_source = f"""
global.window = global;
eval(require("fs").readFileSync({json.dumps(str(RECORDING_PLAN_SOURCE))}, "utf8"));
const ranges = global.AmbientCanvasRecordingPlan.resolveRecordingRanges(
  {json.dumps(recording_source)},
  {chunk_duration_seconds}
);
process.stdout.write(JSON.stringify(ranges));
"""
    completed = subprocess.run(
        ["node", "-e", evaluation_source],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def resolve_fingerprints_for_start_offsets(*start_offsets):
    evaluation_source = f"""
global.window = global;
eval(require("fs").readFileSync({json.dumps(str(RECORDING_FINGERPRINT_SOURCE))}, "utf8"));
(async function () {{
  const fingerprints = [];
  for (const startSeconds of {json.dumps(start_offsets)}) {{
    fingerprints.push(await global.AmbientCanvasRecordingFingerprint.resolveCompositionFingerprint(
      {{ panes: [{{ scene: "bad-apple", options: {{ videoId: "djV11Xbc914" }} }}] }},
      30,
      {{ scenes: {{ "bad-apple": "scene-digest" }}, pipeline: "pipeline-digest" }},
      {{ width: 1920, height: 1080, framesPerSecond: 30 }},
      "#241010",
      startSeconds
    ));
  }}
  process.stdout.write(JSON.stringify(fingerprints));
}})();
"""
    completed = subprocess.run(
        ["node", "-e", evaluation_source],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_full_video_is_divided_into_bounded_sequential_recording_ranges():
    ranges = resolve_recording_ranges(
        {"sequence": "bad-apple:djV11Xbc914", "durationSeconds": 95.05}, 30
    )
    assert ranges == [
        {
            "startSeconds": 0,
            "durationSeconds": 30,
            "sequence": "bad-apple:djV11Xbc914",
        },
        {
            "startSeconds": 30,
            "durationSeconds": 30,
            "sequence": "bad-apple:djV11Xbc914",
        },
        {
            "startSeconds": 60,
            "durationSeconds": 30,
            "sequence": "bad-apple:djV11Xbc914",
        },
        {
            "startSeconds": 90,
            "durationSeconds": 5.05,
            "sequence": "bad-apple:djV11Xbc914",
        },
    ]


def test_non_video_scene_keeps_one_bounded_recording_range():
    assert resolve_recording_ranges(None, 30) == [
        {"startSeconds": 0, "durationSeconds": 30}
    ]


def test_each_source_range_owns_a_distinct_cache_fingerprint():
    fingerprints = resolve_fingerprints_for_start_offsets(0, 30)
    assert len(set(fingerprints)) == 2


def test_recorded_manifest_preserves_sequence_identity():
    uploaded_segments = segment_manifest.parse_uploaded_segment_manifest(
        json.dumps(
            {
                "segments": [
                    {
                        "fingerprint": "first",
                        "extension": "mp4",
                        "durationSeconds": 30,
                        "sequence": "take-on-me",
                    },
                    {
                        "fingerprint": "second",
                        "extension": "mp4",
                        "durationSeconds": 30,
                        "sequence": "take-on-me",
                    },
                ]
            }
        ).encode()
    )
    assert segment_manifest.build_recorded_segment_manifest(uploaded_segments) == {
        "segments": [
            {
                "file": "segments/first.mp4",
                "durationSeconds": 30,
                "sequence": "take-on-me",
            },
            {
                "file": "segments/second.mp4",
                "durationSeconds": 30,
                "sequence": "take-on-me",
            },
        ]
    }


def test_recorded_manifest_rejects_an_invalid_sequence_identity():
    uploaded_segments = segment_manifest.parse_uploaded_segment_manifest(
        json.dumps(
            {
                "segments": [
                    {
                        "fingerprint": "first",
                        "durationSeconds": 30,
                        "sequence": 42,
                    }
                ]
            }
        ).encode()
    )
    assert uploaded_segments is None


def test_playlist_does_not_pin_video_scenes_to_one_excerpt():
    assert "startSeconds" not in PLAYLIST_SOURCE


def test_recording_pipeline_discovers_and_fingerprints_each_source_range():
    assert "resolveRecordingSource" in BAD_APPLE_SOURCE
    assert "resolveCompositionRecordingRanges" in RECORDER_SOURCE
    assert "recordingRange.startSeconds" in RECORDER_SOURCE
    assert DOCUMENT_SOURCE.index(
        "ambient-canvas-recording-plan.js"
    ) < DOCUMENT_SOURCE.index("recorder.js")
