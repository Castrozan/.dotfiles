#!/usr/bin/env python3
import json
import pathlib
import sys

PERSIST_MODE_ON_DISK_ACROSS_RESTARTS = 2
PIPEWIRE_SCREEN_CAPTURE_SOURCE_ID = "pipewire-screen-capture-source"
OBS_SCENES_DIRECTORY = (
    pathlib.Path.home() / ".config" / "obs-studio" / "basic" / "scenes"
)


def iter_pipewire_screen_capture_sources(scene_collection):
    for source in scene_collection.get("sources", []):
        if source.get("id") == PIPEWIRE_SCREEN_CAPTURE_SOURCE_ID:
            yield source


def patch_source_to_persist_restore_across_restarts(source):
    settings = source.setdefault("settings", {})
    if settings.get("RestoreType") == PERSIST_MODE_ON_DISK_ACROSS_RESTARTS:
        return False
    settings["RestoreType"] = PERSIST_MODE_ON_DISK_ACROSS_RESTARTS
    return True


def patch_scene_collection_file(scene_collection_path):
    try:
        scene_collection = json.loads(scene_collection_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        print(f"skip {scene_collection_path.name}: {error}", file=sys.stderr)
        return False

    any_source_patched = False
    for source in iter_pipewire_screen_capture_sources(scene_collection):
        if patch_source_to_persist_restore_across_restarts(source):
            any_source_patched = True

    if any_source_patched:
        scene_collection_path.write_text(json.dumps(scene_collection, indent=4) + "\n")
    return any_source_patched


def patch_every_scene_collection():
    if not OBS_SCENES_DIRECTORY.is_dir():
        return
    for scene_collection_path in OBS_SCENES_DIRECTORY.glob("*.json"):
        if patch_scene_collection_file(scene_collection_path):
            print(f"patched {scene_collection_path.name}: RestoreType=2")


if __name__ == "__main__":
    patch_every_scene_collection()
