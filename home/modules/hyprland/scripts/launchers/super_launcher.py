import subprocess
import time

FUZZEL_SETTLE_DELAY_SECONDS = 0.15


def is_fuzzel_running() -> bool:
    result = subprocess.run(["pgrep", "-x", "fuzzel"], capture_output=True, text=True)
    return result.returncode == 0


def main() -> None:
    if is_fuzzel_running():
        subprocess.run(["pkill", "-x", "fuzzel"])
        return

    subprocess.run(["hypr-ensure-workspace-tiled"])
    subprocess.run(["hypr-fuzzel"])
    time.sleep(FUZZEL_SETTLE_DELAY_SECONDS)
    subprocess.run(["hypr-ensure-workspace-grouped"])


if __name__ == "__main__":
    main()
