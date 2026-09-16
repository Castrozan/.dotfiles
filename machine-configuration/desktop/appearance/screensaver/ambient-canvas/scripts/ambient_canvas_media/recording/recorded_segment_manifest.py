import json

RECORDED_SEGMENT_DIRECTORY_NAME = "segments"
DEFAULT_RECORDED_SEGMENT_EXTENSION = "mp4"


def build_recorded_segment_relative_path(segment_fingerprint, extension):
    return f"{RECORDED_SEGMENT_DIRECTORY_NAME}/{segment_fingerprint}.{extension}"


def segment_sequence_is_valid(segment):
    return "sequence" not in segment or (
        isinstance(segment["sequence"], str) and segment["sequence"]
    )


def parse_uploaded_segment_manifest(uploaded_manifest_bytes):
    try:
        decoded_manifest = json.loads(uploaded_manifest_bytes)
    except (TypeError, ValueError):
        return None
    if not isinstance(decoded_manifest, dict):
        return None
    uploaded_segments = decoded_manifest.get("segments")
    if not isinstance(uploaded_segments, list) or not uploaded_segments:
        return None
    if not all(
        isinstance(uploaded_segment, dict)
        and uploaded_segment.get("fingerprint")
        and uploaded_segment.get("durationSeconds")
        and segment_sequence_is_valid(uploaded_segment)
        for uploaded_segment in uploaded_segments
    ):
        return None
    return uploaded_segments


def build_recorded_segment_manifest(uploaded_segments):
    return {
        "segments": [
            {
                "file": build_recorded_segment_relative_path(
                    uploaded_segment["fingerprint"],
                    uploaded_segment.get(
                        "extension", DEFAULT_RECORDED_SEGMENT_EXTENSION
                    ),
                ),
                "durationSeconds": uploaded_segment["durationSeconds"],
                **(
                    {"sequence": uploaded_segment["sequence"]}
                    if uploaded_segment.get("sequence")
                    else {}
                ),
            }
            for uploaded_segment in uploaded_segments
        ]
    }


def parse_recorded_segment_manifest(manifest_bytes):
    try:
        decoded_manifest = json.loads(manifest_bytes)
    except (TypeError, ValueError):
        return None
    if not isinstance(decoded_manifest, dict):
        return None
    recorded_segments = decoded_manifest.get("segments")
    if not isinstance(recorded_segments, list) or not recorded_segments:
        return None
    if not all(
        isinstance(recorded_segment, dict)
        and recorded_segment.get("file")
        and segment_sequence_is_valid(recorded_segment)
        for recorded_segment in recorded_segments
    ):
        return None
    return decoded_manifest
