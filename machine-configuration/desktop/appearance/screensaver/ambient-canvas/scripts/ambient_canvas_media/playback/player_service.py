import logging
import os
import shutil
import subprocess
import sys

PLAYER_SERVICE_NAME = "ambient-canvas-player"
PLAYER_LAUNCHD_LABEL = "com.dotfiles.ambient-canvas-player"
PLAYER_RESTART_TIMEOUT_SECONDS = 15
LAUNCHER_LOGGER_NAME = "ambient_canvas.launcher"


def build_player_restart_command(platform_name, user_id):
    if platform_name == "darwin":
        return [
            shutil.which("launchctl") or "/bin/launchctl",
            "kickstart",
            "-k",
            f"gui/{user_id}/{PLAYER_LAUNCHD_LABEL}",
        ]
    return [
        shutil.which("systemctl") or "/run/current-system/sw/bin/systemctl",
        "--user",
        "restart",
        f"{PLAYER_SERVICE_NAME}.service",
    ]


def restart_player_service():
    logger = logging.getLogger(LAUNCHER_LOGGER_NAME)
    try:
        completed = subprocess.run(
            build_player_restart_command(sys.platform, os.getuid()),
            check=False,
            capture_output=True,
            timeout=PLAYER_RESTART_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        logger.error("player_restart_failed error=%s", error)
        return False
    if completed.returncode != 0:
        logger.error(
            "player_restart_failed exit_code=%s output=%s",
            completed.returncode,
            completed.stderr.decode(errors="replace").strip(),
        )
        return False
    logger.info("player_restart_requested")
    return True
