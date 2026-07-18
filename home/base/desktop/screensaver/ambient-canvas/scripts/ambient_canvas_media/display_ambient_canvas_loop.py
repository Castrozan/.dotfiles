import argparse
import os
import subprocess
import sys
import urllib.parse

from ambient_canvas_browser import (
    read_screen_dimensions,
    resolve_centered_window_geometry,
    resolve_chromium_browser_application,
)

DEFAULT_DISPLAY_PROFILE_DIRECTORY = os.path.expanduser(
    "~/.local/state/ambient-canvas/profile"
)


def resolve_player_page_path(index_file_path):
    return os.path.join(os.path.dirname(index_file_path), "player-video.html")


def resolve_recorded_loop_source_url(output_directory):
    pointer_path = os.path.join(output_directory, "loop.current")
    if not os.path.isfile(pointer_path):
        return None
    with open(pointer_path) as pointer_file:
        media_filename = pointer_file.read().strip()
    if not media_filename:
        return None
    media_path = os.path.join(output_directory, media_filename)
    if not os.path.isfile(media_path):
        return None
    return "file://" + urllib.parse.quote(media_path)


def build_display_url(player_page_path, recorded_loop_source_url):
    source_query = urllib.parse.urlencode({"src": recorded_loop_source_url})
    return f"file://{player_page_path}?{source_query}"


def build_display_browser_arguments(
    browser_application, display_url, display_profile_directory, geometry
):
    window_width, window_height, window_left, window_top = geometry
    return [
        "open",
        "-na",
        browser_application,
        "--args",
        f"--app={display_url}",
        f"--user-data-dir={display_profile_directory}",
        f"--window-size={window_width},{window_height}",
        f"--window-position={window_left},{window_top}",
        "--no-first-run",
        "--no-default-browser-check",
        "--autoplay-policy=no-user-gesture-required",
        "--allow-file-access-from-files",
        "--disable-translate",
    ]


def launch_display(index_file_path, output_directory, display_profile_directory):
    browser_application = resolve_chromium_browser_application()
    if browser_application is None:
        print(
            "display-ambient-canvas-loop: no Chromium browser installed",
            file=sys.stderr,
        )
        return 1
    recorded_loop_source_url = resolve_recorded_loop_source_url(output_directory)
    if recorded_loop_source_url is None:
        print("display-ambient-canvas-loop: no recorded loop to play", file=sys.stderr)
        return 1
    subprocess.run(
        build_display_browser_arguments(
            browser_application,
            build_display_url(
                resolve_player_page_path(index_file_path), recorded_loop_source_url
            ),
            display_profile_directory,
            resolve_centered_window_geometry(*read_screen_dimensions()),
        ),
        check=True,
    )
    return 0


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--output-directory", required=True)
    argument_parser.add_argument(
        "--profile-directory", default=DEFAULT_DISPLAY_PROFILE_DIRECTORY
    )
    parsed_arguments = argument_parser.parse_args()

    index_file_path = os.environ.get("AMBIENT_CANVAS_INDEX")
    if not index_file_path or not os.path.isfile(index_file_path):
        print("display-ambient-canvas-loop: web assets not found", file=sys.stderr)
        return 1

    return launch_display(
        index_file_path,
        parsed_arguments.output_directory,
        parsed_arguments.profile_directory,
    )


if __name__ == "__main__":
    sys.exit(main())
