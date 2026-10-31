import json
import subprocess
import time
import urllib.error
import urllib.request


SERVICES = ("avatar-audio", "avatar-control-server", "avatar-renderer", "avatar-camera")


def service_failed():
    failed = subprocess.run(
        ["systemctl", "--user", "is-failed", *SERVICES], capture_output=True, text=True
    )
    return "failed" in failed.stdout.splitlines()


def renderer_ready():
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8766/health", timeout=1
        ) as response:
            return json.load(response).get("rendererConnected")
    except (urllib.error.URLError, TimeoutError):
        return False


def camera_ready():
    capture = subprocess.run(
        ["v4l2-ctl", "-d", "/dev/video10", "--info"], capture_output=True, text=True
    )
    return capture.returncode == 0 and "Video Capture" in capture.stdout


def wait_until_ready(timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if service_failed():
            raise RuntimeError(
                "An avatar service failed; inspect systemctl --user status avatar-*"
            )
        if renderer_ready() and camera_ready():
            return
        time.sleep(0.25)
    raise TimeoutError("The avatar renderer did not become ready")


def audio_ready():
    result = subprocess.run(["avatar-audio", "status"], capture_output=True, text=True)
    if result.returncode:
        return False
    return json.loads(result.stdout).get("running", False)


def main():
    try:
        if not audio_ready():
            subprocess.run(["systemctl", "--user", "stop", "avatar.target"], check=True)
        subprocess.run(["systemctl", "--user", "start", "avatar.target"], check=True)
        wait_until_ready()
        if not audio_ready():
            raise RuntimeError("The avatar audio graph did not become ready")
    except BaseException:
        subprocess.run(["systemctl", "--user", "stop", "avatar.target"], check=False)
        raise
    print(
        "Avatar ready. Check mute/levels with avatar-audio status. Run avatar-controls for video controls"
    )


if __name__ == "__main__":
    main()
