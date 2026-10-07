import json
import os
import subprocess
import time

from shorts_browser import browser_instance
from shorts_store import read_document


def start_profile(configuration, binary):
    profiles = subprocess.run(
        [binary, "profiles", "--json"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if not any(
        profile.get("id") == configuration["browser_profile_id"]
        and profile.get("name") == configuration["browser_profile"]
        and profile.get("pathExists") is True
        for profile in json.loads(profiles.stdout)
    ):
        raise ValueError("The existing Shorts profile must be present before startup")
    subprocess.run(
        [
            binary,
            "instance",
            "start",
            "--profile",
            configuration["browser_profile"],
            "--mode",
            "headed",
            "--port",
            "9868",
        ],
        check=True,
        capture_output=True,
        timeout=15,
    )


def main():
    binary = os.environ["SHORTS_PINCHTAB"]
    configuration = read_document(os.environ["SHORTS_CONFIGURATION"])
    for _ in range(30):
        controller = subprocess.run(
            [binary, "instances", "--json"], capture_output=True, timeout=5
        )
        if controller.returncode == 0:
            break
        time.sleep(1)
    else:
        raise ValueError("Browser controller did not become ready")
    start_profile(configuration, binary)
    for _ in range(30):
        try:
            instance = browser_instance(configuration)
            health = subprocess.run(
                [binary, "--server", instance["url"], "health"],
                capture_output=True,
                timeout=5,
            )
            if health.returncode == 0:
                return
        except (ValueError, subprocess.TimeoutExpired):
            pass
        time.sleep(1)
    raise ValueError("The exact Shorts browser did not become ready")


if __name__ == "__main__":
    main()
