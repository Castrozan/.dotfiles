import json
import subprocess
import time
import urllib.error
import urllib.request


SERVICES = ("avatar-audio", "avatar-control-server", "avatar-renderer", "avatar-camera")


def wait_until_ready(timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        failed = subprocess.run(
            ["systemctl", "--user", "is-failed", *SERVICES],
            capture_output=True,
            text=True,
        )
        if "failed" in failed.stdout.splitlines():
            raise RuntimeError(
                "An avatar service failed; inspect systemctl --user status avatar-*"
            )
        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:8766/health", timeout=1
            ) as response:
                if json.load(response).get("rendererConnected"):
                    capture = subprocess.run(
                        ["v4l2-ctl", "-d", "/dev/video10", "--info"],
                        capture_output=True,
                        text=True,
                    )
                    if capture.returncode == 0 and "Video Capture" in capture.stdout:
                        return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.25)
    raise TimeoutError("The avatar renderer did not become ready")


def main():
    try:
        subprocess.run(["systemctl", "--user", "start", "avatar.target"], check=True)
        wait_until_ready()
    except BaseException:
        subprocess.run(["systemctl", "--user", "stop", "avatar.target"], check=False)
        raise
    print(
        "Avatar ready. Audio inputs start muted. Controls: http://localhost:3000/controls.html"
    )


if __name__ == "__main__":
    main()
