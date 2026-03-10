import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_screenshots_directory() -> Path:
    pictures_dir = os.environ.get("XDG_PICTURES_DIR", str(Path.home() / "Pictures"))
    return Path(pictures_dir) / "Screenshots"


def generate_screenshot_filename() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return f"{timestamp}_screenshot.png"


def capture_region_screenshot(save_path: Path) -> bool:
    slurp_result = subprocess.run(["slurp", "-d"], capture_output=True, text=True)
    if slurp_result.returncode != 0:
        return False
    geometry = slurp_result.stdout.strip()
    subprocess.run(["grim", "-g", geometry, str(save_path)])
    return True


def capture_active_window_screenshot(save_path: Path) -> bool:
    result = subprocess.run(
        ["hyprctl", "activewindow", "-j"], capture_output=True, text=True
    )
    window_data = json.loads(result.stdout)
    at_x, at_y = window_data["at"]
    width, height = window_data["size"]
    geometry = f"{at_x},{at_y} {width}x{height}"

    if not geometry or geometry == "null":
        subprocess.run(["notify-send", "Screenshot", "No active window", "-t", "2000"])
        return False

    subprocess.run(["grim", "-g", geometry, str(save_path)])
    return True


def capture_focused_monitor_screenshot(save_path: Path) -> bool:
    result = subprocess.run(
        ["hyprctl", "monitors", "-j"], capture_output=True, text=True
    )
    monitors = json.loads(result.stdout)
    focused_monitor = next((m for m in monitors if m.get("focused")), None)
    if focused_monitor is None:
        return False

    geometry = (
        f"{focused_monitor['x']},{focused_monitor['y']}"
        f" {focused_monitor['width']}x{focused_monitor['height']}"
    )
    subprocess.run(["grim", "-g", geometry, str(save_path)])
    return True


def capture_full_screen_screenshot(save_path: Path) -> bool:
    subprocess.run(["grim", str(save_path)])
    return True


def capture_and_annotate_screenshot(save_path: Path) -> Path | None:
    slurp_result = subprocess.run(["slurp", "-d"], capture_output=True, text=True)
    if slurp_result.returncode != 0:
        return None
    geometry = slurp_result.stdout.strip()
    subprocess.run(["grim", "-g", geometry, str(save_path)])

    annotated_path = save_path.with_name(save_path.stem + "_annotated.png")
    env = os.environ.copy()
    env["GSK_RENDERER"] = "gl"
    subprocess.run(
        ["satty", "-f", str(save_path), "-o", str(annotated_path)],
        env=env,
    )

    if annotated_path.is_file():
        return annotated_path
    return save_path


def copy_screenshot_to_clipboard_and_notify(save_path: Path) -> None:
    with open(save_path, "rb") as screenshot_file:
        subprocess.run(["wl-copy"], stdin=screenshot_file)

    subprocess.run(
        [
            "notify-send",
            "Screenshot saved",
            str(save_path),
            "-i",
            str(save_path),
            "-t",
            "3000",
        ]
    )


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "region"
    screenshots_dir = get_screenshots_directory()
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    save_path = screenshots_dir / generate_screenshot_filename()

    should_copy_to_clipboard = True

    match mode:
        case "region":
            if not capture_region_screenshot(save_path):
                return
        case "window":
            if not capture_active_window_screenshot(save_path):
                raise SystemExit(1)
        case "output" | "monitor":
            if not capture_focused_monitor_screenshot(save_path):
                raise SystemExit(1)
        case "screen":
            capture_full_screen_screenshot(save_path)
        case "annotate":
            should_copy_to_clipboard = False
            result_path = capture_and_annotate_screenshot(save_path)
            if result_path is None:
                return
            save_path = result_path
        case _:
            print(
                "Usage: hypr-screenshot [region|window|output|screen|annotate]",
                file=sys.stderr,
            )
            raise SystemExit(1)

    if should_copy_to_clipboard:
        copy_screenshot_to_clipboard_and_notify(save_path)


if __name__ == "__main__":
    main()
