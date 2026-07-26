import hashlib
import os
import re

SCENE_FACTORY_REGISTRATION_PATTERN = re.compile(
    r"AMBIENT_CANVAS_SCENE_FACTORIES\[\s*\"([^\"]+)\"\s*\]\s*="
)
SCENES_DIRECTORY_NAME = "scenes"
RECORDING_PIPELINE_RELATIVE_PATHS = (
    "player.js",
    "recorder.js",
    "record/ambient-canvas-recording-compositor.js",
    "record/ambient-canvas-recording-encoder.js",
    "record/ambient-canvas-recording-fingerprint.js",
    "vendor/mp4-muxer.min.js",
)


def digest_source_files(source_file_paths):
    accumulated_digest = hashlib.sha256()
    for source_file_path in sorted(source_file_paths):
        accumulated_digest.update(os.path.basename(source_file_path).encode())
        with open(source_file_path, "rb") as source_file:
            accumulated_digest.update(source_file.read())
    return accumulated_digest.hexdigest()


def resolve_scene_source_file_paths(registering_source_path, scenes_directory):
    containing_directory = os.path.dirname(registering_source_path)
    if os.path.abspath(containing_directory) == os.path.abspath(scenes_directory):
        return [registering_source_path]
    return [
        os.path.join(containing_directory, file_name)
        for file_name in os.listdir(containing_directory)
        if file_name.endswith(".js")
    ]


def map_scene_names_to_source_files(served_web_directory):
    scenes_directory = os.path.join(served_web_directory, SCENES_DIRECTORY_NAME)
    scene_source_files = {}
    for directory_path, _, file_names in os.walk(scenes_directory):
        for file_name in sorted(file_names):
            if not file_name.endswith(".js"):
                continue
            registering_source_path = os.path.join(directory_path, file_name)
            with open(registering_source_path) as scene_source_file:
                scene_source_text = scene_source_file.read()
            for scene_name in SCENE_FACTORY_REGISTRATION_PATTERN.findall(
                scene_source_text
            ):
                scene_source_files[scene_name] = resolve_scene_source_file_paths(
                    registering_source_path, scenes_directory
                )
    return scene_source_files


def build_scene_source_digests(served_web_directory):
    return {
        scene_name: digest_source_files(source_file_paths)
        for scene_name, source_file_paths in map_scene_names_to_source_files(
            served_web_directory
        ).items()
    }


def build_recording_pipeline_digest(served_web_directory):
    return digest_source_files(
        [
            os.path.join(served_web_directory, relative_path)
            for relative_path in RECORDING_PIPELINE_RELATIVE_PATHS
        ]
    )


def build_segment_fingerprint_inputs(served_web_directory):
    return {
        "scenes": build_scene_source_digests(served_web_directory),
        "pipeline": build_recording_pipeline_digest(served_web_directory),
    }
