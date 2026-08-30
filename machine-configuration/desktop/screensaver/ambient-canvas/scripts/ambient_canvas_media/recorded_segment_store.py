import json
import os
import tempfile

from recorded_segment_manifest import (
    RECORDED_SEGMENT_DIRECTORY_NAME,
    build_recorded_segment_relative_path,
    parse_recorded_segment_manifest,
)

RECORDED_LOOP_DIRECTORY_NAME = "loops"
RECORDED_SEGMENT_MANIFEST_FILENAME = "loop.segments.json"
RECORDED_SOURCE_IDENTIFIER_FILENAME = "loop.source"


def resolve_recorded_loop_directory(state_directory, capture_signature):
    return os.path.join(
        state_directory, RECORDED_LOOP_DIRECTORY_NAME, capture_signature
    )


def resolve_recorded_segment_directory(output_directory):
    return os.path.join(output_directory, RECORDED_SEGMENT_DIRECTORY_NAME)


def resolve_recorded_segment_manifest_path(output_directory):
    return os.path.join(output_directory, RECORDED_SEGMENT_MANIFEST_FILENAME)


def list_recorded_segment_fingerprints(output_directory):
    segment_directory = resolve_recorded_segment_directory(output_directory)
    if not os.path.isdir(segment_directory):
        return []
    return sorted(
        os.path.splitext(segment_file_name)[0]
        for segment_file_name in os.listdir(segment_directory)
        if not segment_file_name.endswith(".staging")
    )


def store_recorded_segment(
    output_directory, segment_fingerprint, extension, recorded_bytes
):
    segment_directory = resolve_recorded_segment_directory(output_directory)
    os.makedirs(segment_directory, exist_ok=True)
    staging_descriptor, staging_path = tempfile.mkstemp(
        dir=segment_directory, suffix=".staging"
    )
    with os.fdopen(staging_descriptor, "wb") as staging_file:
        staging_file.write(recorded_bytes)
    stored_path = os.path.join(
        output_directory,
        build_recorded_segment_relative_path(segment_fingerprint, extension),
    )
    os.replace(staging_path, stored_path)
    return stored_path


def resolve_manifest_segment_paths(output_directory, recorded_manifest):
    return [
        os.path.join(output_directory, recorded_segment["file"])
        for recorded_segment in recorded_manifest["segments"]
    ]


def list_missing_manifest_segment_positions(output_directory, recorded_manifest):
    return [
        position
        for position, segment_path in enumerate(
            resolve_manifest_segment_paths(output_directory, recorded_manifest), start=1
        )
        if not os.path.isfile(segment_path)
    ]


def manifest_segments_are_all_present(output_directory, recorded_manifest):
    return not list_missing_manifest_segment_positions(
        output_directory, recorded_manifest
    )


def write_recorded_segment_manifest(output_directory, recorded_manifest):
    manifest_path = resolve_recorded_segment_manifest_path(output_directory)
    with open(manifest_path, "w") as manifest_file:
        json.dump(recorded_manifest, manifest_file, indent=2)
    return manifest_path


def read_recorded_segment_manifest(output_directory):
    manifest_path = resolve_recorded_segment_manifest_path(output_directory)
    if not os.path.isfile(manifest_path):
        return None
    with open(manifest_path, "rb") as manifest_file:
        return parse_recorded_segment_manifest(manifest_file.read())


def resolve_playable_segment_manifest_path(output_directory):
    recorded_manifest = read_recorded_segment_manifest(output_directory)
    if recorded_manifest is None:
        return None
    if not manifest_segments_are_all_present(output_directory, recorded_manifest):
        return None
    return resolve_recorded_segment_manifest_path(output_directory)


def prune_recorded_segments_outside_manifest(output_directory, recorded_manifest):
    retained_segment_paths = {
        os.path.abspath(segment_path)
        for segment_path in resolve_manifest_segment_paths(
            output_directory, recorded_manifest
        )
    }
    segment_directory = resolve_recorded_segment_directory(output_directory)
    if not os.path.isdir(segment_directory):
        return []
    pruned_segment_paths = []
    for segment_file_name in sorted(os.listdir(segment_directory)):
        segment_path = os.path.join(segment_directory, segment_file_name)
        if os.path.abspath(segment_path) in retained_segment_paths:
            continue
        os.remove(segment_path)
        pruned_segment_paths.append(segment_path)
    return pruned_segment_paths


def write_recorded_source_identifier(output_directory, source_identifier):
    source_path = os.path.join(output_directory, RECORDED_SOURCE_IDENTIFIER_FILENAME)
    with open(source_path, "w") as source_file:
        source_file.write(source_identifier + "\n")


def read_recorded_source_identifier(output_directory):
    source_path = os.path.join(output_directory, RECORDED_SOURCE_IDENTIFIER_FILENAME)
    if not os.path.isfile(source_path):
        return None
    with open(source_path) as source_file:
        return source_file.read().strip()
