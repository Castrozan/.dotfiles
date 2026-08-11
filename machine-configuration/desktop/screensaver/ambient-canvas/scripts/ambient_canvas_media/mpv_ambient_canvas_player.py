import os
import subprocess
import tempfile
import threading
import time

from ambient_canvas_mpv_visibility import (
    VisibilityGatedPlaybackController,
    pin_player_window_to_workspace,
)
from ambient_canvas_playback_dwell_override import effective_dwell_seconds
from ambient_canvas_shuffled_segment_order import ShuffledSegmentOrder
from mpv_ambient_canvas_ipc import (
    MpvIpcClient,
    wait_for_end_of_file,
)
from recorded_segment_store import (
    read_recorded_segment_manifest,
    resolve_manifest_segment_paths,
)

TARGET_WORKSPACE_ID = 11


def build_mpv_arguments(socket_path):
    return [
        "mpv",
        "--no-terminal",
        f"--input-ipc-server={socket_path}",
        "--vo=gpu",
        "--gpu-context=wayland",
        "--force-window=yes",
        "--audio=no",
        "--title=ambient-canvas-gpu-screensaver",
        "--no-osc",
        "--no-input-default-bindings",
        "--idle",
        "--loop-file=no",
    ]


def resolve_segment_dwell(segment, playback_dwell_override_path):
    return effective_dwell_seconds(
        segment["durationSeconds"], playback_dwell_override_path
    )


def play_single_segment_forever(
    mpv_client, segment, segment_file_path, dwell_override_path
):
    mpv_client.send_command(["loadfile", segment_file_path, "replace"])
    mpv_client.send_command(["set_property", "loop-file", "inf"])
    dwell = resolve_segment_dwell(segment, dwell_override_path)
    mpv_client.send_command(["set_property", "length", str(dwell)])


def play_shuffled_loop(mpv_client, segments, segment_file_paths, dwell_override_path):
    segment_order = ShuffledSegmentOrder(len(segments))
    while True:
        segment_index = segment_order.next_segment_index()
        segment = segments[segment_index]
        mpv_client.send_command(
            ["loadfile", segment_file_paths[segment_index], "replace"]
        )
        dwell = resolve_segment_dwell(segment, dwell_override_path)
        mpv_client.send_command(["set_property", "length", str(dwell)])
        wait_for_end_of_file(mpv_client)


def run_player(segment_manifest_path, playback_dwell_override_path):
    loop_directory = os.path.dirname(segment_manifest_path)
    recorded_manifest = read_recorded_segment_manifest(loop_directory)
    if recorded_manifest is None:
        return 1
    segments = recorded_manifest["segments"]
    if not segments:
        return 1
    segment_file_paths = resolve_manifest_segment_paths(
        loop_directory, recorded_manifest
    )

    socket_path = os.path.join(
        tempfile.gettempdir(), f"ambient-canvas-{os.getpid()}.sock"
    )
    mpv_process = subprocess.Popen(
        build_mpv_arguments(socket_path),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    mpv_client = MpvIpcClient(socket_path).connect()
    window_pin_thread = threading.Thread(
        target=pin_player_window_to_workspace, daemon=True
    )
    window_pin_thread.start()

    visibility_controller = VisibilityGatedPlaybackController(
        mpv_client, TARGET_WORKSPACE_ID
    )
    visibility_controller.start()

    try:
        if len(segments) == 1:
            play_single_segment_forever(
                mpv_client,
                segments[0],
                segment_file_paths[0],
                playback_dwell_override_path,
            )
            while mpv_process.poll() is None:
                time.sleep(1)
        else:
            play_shuffled_loop(
                mpv_client,
                segments,
                segment_file_paths,
                playback_dwell_override_path,
            )
    finally:
        visibility_controller.stop()
        mpv_client.close()
        mpv_process.terminate()
        try:
            mpv_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            mpv_process.kill()
        try:
            os.remove(socket_path)
        except OSError:
            pass
    return 0
