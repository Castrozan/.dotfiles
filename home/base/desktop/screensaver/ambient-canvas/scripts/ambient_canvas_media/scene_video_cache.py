import json
import os
import subprocess
import sys

SCENE_VIDEO_MANIFEST_FILENAME = "scene-videos.json"
SCENE_VIDEO_DIRECTORY_NAME = "videos"
YT_DLP_FORMAT_SELECTOR = "18/best[height<=480][ext=mp4]"
DOWNLOAD_TIMEOUT_SECONDS = 300


def resolve_scene_video_directory(output_directory):
    return os.path.join(output_directory, SCENE_VIDEO_DIRECTORY_NAME)


def read_scene_video_manifest(served_web_directory):
    manifest_path = os.path.join(served_web_directory, SCENE_VIDEO_MANIFEST_FILENAME)
    if not os.path.isfile(manifest_path):
        return []
    with open(manifest_path) as manifest_file:
        manifest = json.load(manifest_file)
    return manifest.get("videos", [])


def build_download_arguments(video_id, destination_path):
    return [
        "yt-dlp",
        "--no-warnings",
        "--quiet",
        "--no-playlist",
        "--format",
        YT_DLP_FORMAT_SELECTOR,
        "--output",
        destination_path,
        f"https://www.youtube.com/watch?v={video_id}",
    ]


def download_missing_scene_videos(served_web_directory, output_directory):
    scene_video_directory = resolve_scene_video_directory(output_directory)
    os.makedirs(scene_video_directory, exist_ok=True)
    downloaded_video_ids = []
    for scene_video in read_scene_video_manifest(served_web_directory):
        video_id = scene_video["id"]
        destination_path = os.path.join(scene_video_directory, f"{video_id}.mp4")
        if os.path.isfile(destination_path):
            continue
        completed = subprocess.run(
            build_download_arguments(video_id, destination_path),
            check=False,
            capture_output=True,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
        )
        if completed.returncode != 0 or not os.path.isfile(destination_path):
            print(
                f"ambient-canvas: scene video {video_id} could not be downloaded",
                file=sys.stderr,
            )
            continue
        downloaded_video_ids.append(video_id)
    return downloaded_video_ids
