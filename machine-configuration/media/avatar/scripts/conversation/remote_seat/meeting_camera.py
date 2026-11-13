import json
import pathlib
import subprocess

import local_seat

OBS_APPLICATION = pathlib.Path("/Applications/OBS.app")
OBS_SUPPORT = pathlib.Path("Library/Application Support/obs-studio/basic")
PROFILE_NAME = "Avatar"
COLLECTION_NAME = "Avatar"
SCENE_NAME = "Avatar"
SOURCE_NAME = "Avatar"
AVATAR_VIEW_URL = f"http://localhost:{local_seat.WINDOW_PORT}/?viewer&bare"
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FRAMES_PER_SECOND = 30
COLLECTION_FLAG = f"--collection {COLLECTION_NAME}"
LAUNCH_COMMAND = [
    "/usr/bin/open",
    "-g",
    "-n",
    "-a",
    "OBS",
    "--args",
    "--collection",
    COLLECTION_NAME,
    "--profile",
    PROFILE_NAME,
    "--scene",
    SCENE_NAME,
    "--startvirtualcam",
    "--disable-updater",
    "--disable-missing-files-check",
    "--multi",
]


def avatar_browser_source():
    return {
        "id": "browser_source",
        "versioned_id": "browser_source",
        "name": SOURCE_NAME,
        "enabled": True,
        "muted": False,
        "volume": 1.0,
        "settings": {
            "url": AVATAR_VIEW_URL,
            "width": FRAME_WIDTH,
            "height": FRAME_HEIGHT,
            "fps": FRAMES_PER_SECOND,
            "fps_custom": True,
        },
    }


def avatar_scene_item():
    return {
        "id": 1,
        "name": SOURCE_NAME,
        "visible": True,
        "locked": False,
        "pos": {"x": 0.0, "y": 0.0},
        "scale": {"x": 1.0, "y": 1.0},
        "rot": 0.0,
        "bounds_type": 0,
    }


def avatar_scene():
    return {
        "id": "scene",
        "versioned_id": "scene",
        "name": SCENE_NAME,
        "enabled": True,
        "settings": {"id_counter": 1, "items": [avatar_scene_item()]},
    }


def scene_collection():
    return {
        "name": COLLECTION_NAME,
        "current_scene": SCENE_NAME,
        "current_program_scene": SCENE_NAME,
        "scene_order": [{"name": SCENE_NAME}],
        "sources": [avatar_browser_source(), avatar_scene()],
        "groups": [],
        "transitions": [],
        "quick_transitions": [],
    }


def profile_settings():
    return "\n".join(
        [
            "[General]",
            f"Name={PROFILE_NAME}",
            "",
            "[Video]",
            f"BaseCX={FRAME_WIDTH}",
            f"BaseCY={FRAME_HEIGHT}",
            f"OutputCX={FRAME_WIDTH}",
            f"OutputCY={FRAME_HEIGHT}",
            "FPSType=0",
            f"FPSCommon={FRAMES_PER_SECOND}",
            "",
        ]
    )


def write_configuration():
    support = pathlib.Path.home() / OBS_SUPPORT
    scenes = support / "scenes"
    profile = support / "profiles" / PROFILE_NAME
    scenes.mkdir(parents=True, exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)
    (scenes / f"{COLLECTION_NAME}.json").write_text(
        json.dumps(scene_collection(), indent=4)
    )
    (profile / "basic.ini").write_text(profile_settings())


def stop():
    local_seat.end_processes_matching(COLLECTION_FLAG)


def start():
    if not OBS_APPLICATION.exists():
        raise RuntimeError(f"OBS Studio is not installed: {OBS_APPLICATION} is missing")
    write_configuration()
    stop()
    subprocess.run(
        LAUNCH_COMMAND, check=True, timeout=local_seat.COMMAND_TIMEOUT_SECONDS
    )
