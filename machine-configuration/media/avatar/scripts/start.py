import json
import subprocess
import time
import urllib.error
import urllib.request


MEETING_TARGET = "avatar.target"
SERVICES = (
    "avatar-audio",
    "avatar-control-server",
    "avatar-renderer",
    "avatar-browser",
    "avatar-camera",
)


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


def wait_until_ready(readiness_checks, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if service_failed():
            raise RuntimeError(
                "An avatar service failed; inspect systemctl --user status avatar-*"
            )
        if all(check() for check in readiness_checks):
            return
        time.sleep(0.25)
    raise TimeoutError("The avatar renderer did not become ready")


def audio_ready():
    result = subprocess.run(["avatar-audio", "status"], capture_output=True, text=True)
    if result.returncode:
        return False
    return json.loads(result.stdout).get("running", False)


def bring_up(target, readiness_checks):
    try:
        if not audio_ready():
            subprocess.run(["systemctl", "--user", "stop", MEETING_TARGET], check=True)
        subprocess.run(["systemctl", "--user", "start", target], check=True)
        wait_until_ready(readiness_checks)
        if not audio_ready():
            raise RuntimeError("The avatar audio graph did not become ready")
    except BaseException:
        subprocess.run(["systemctl", "--user", "stop", target], check=False)
        raise


def main():
    bring_up(MEETING_TARGET, (renderer_ready, camera_ready))
    subprocess.run(["avatar-audio", "open"], check=True, stdout=subprocess.DEVNULL)
    print(
        "Avatar ready with her voice and the default microphone open. Check levels with avatar-audio status. Switch video with avatar-command mode"
    )


if __name__ == "__main__":
    main()
