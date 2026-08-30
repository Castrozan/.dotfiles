import sys

from recorded_segment_manifest import (
    build_recorded_segment_manifest,
    parse_uploaded_segment_manifest,
)
from recorded_segment_store import (
    list_missing_manifest_segment_positions,
    prune_recorded_segments_outside_manifest,
    write_recorded_segment_manifest,
    write_recorded_source_identifier,
)


def commit_recorded_segment_manifest(
    output_directory, uploaded_manifest_bytes, source_identifier
):
    uploaded_segments = parse_uploaded_segment_manifest(uploaded_manifest_bytes)
    if uploaded_segments is None:
        print("render-ambient-canvas-loop: recording did not complete", file=sys.stderr)
        return None
    recorded_manifest = build_recorded_segment_manifest(uploaded_segments)
    missing_positions = list_missing_manifest_segment_positions(
        output_directory, recorded_manifest
    )
    if missing_positions:
        print(
            "render-ambient-canvas-loop: no segment was stored for playlist "
            f"composition {', '.join(str(position) for position in missing_positions)}",
            file=sys.stderr,
        )
        return None
    manifest_path = write_recorded_segment_manifest(output_directory, recorded_manifest)
    prune_recorded_segments_outside_manifest(output_directory, recorded_manifest)
    write_recorded_source_identifier(output_directory, source_identifier)
    return manifest_path
