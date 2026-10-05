import os
import plistlib
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path


LAUNCH_AGENT_LABEL = "org.nix-community.home.activate-agenix"
LAUNCH_AGENT_TIMEOUT_SECONDS = 10.0


def disable_restart_loop(plist_path: Path) -> None:
    configuration = plistlib.loads(plist_path.read_bytes())
    configuration["KeepAlive"] = False
    plist_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    try:
        plist_path.write_bytes(plistlib.dumps(configuration))
    finally:
        plist_path.chmod(0o444)


def stop_launch_agent(domain: str) -> None:
    service_target = f"{domain}/{LAUNCH_AGENT_LABEL}"
    subprocess.run(
        ["/bin/launchctl", "bootout", service_target],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=2,
        check=False,
    )
    deadline = time.monotonic() + LAUNCH_AGENT_TIMEOUT_SECONDS
    while True:
        result = subprocess.run(
            ["/bin/launchctl", "print", service_target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
        if result.returncode != 0:
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Launch agent did not stop: {service_target}")
        time.sleep(0.5)


def remove_abandoned_generations(temporary_root: Path) -> None:
    generations = temporary_root / "agenix.d"
    if not generations.is_dir():
        return
    live_generation = (temporary_root / "agenix").resolve()
    for generation in generations.iterdir():
        if generation.resolve() == live_generation or not generation.is_dir():
            continue
        if generation.is_symlink():
            generation.unlink()
            continue
        for entry in [generation, *generation.rglob("*")]:
            if not entry.is_symlink():
                entry.chmod(entry.stat().st_mode | stat.S_IWUSR)
        shutil.rmtree(generation)


def bootstrap_launch_agent(domain: str, plist_path: Path) -> None:
    deadline = time.monotonic() + LAUNCH_AGENT_TIMEOUT_SECONDS
    while True:
        result = subprocess.run(
            ["/bin/launchctl", "bootstrap", domain, str(plist_path)],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0:
            return
        if time.monotonic() >= deadline:
            raise subprocess.CalledProcessError(
                result.returncode, result.args, result.stdout, result.stderr
            )
        time.sleep(0.5)


def restart_agenix_launch_agent(home_directory: Path) -> None:
    plist_path = home_directory / "Library/LaunchAgents" / f"{LAUNCH_AGENT_LABEL}.plist"
    if not plist_path.is_file():
        return
    disable_restart_loop(plist_path)
    domain = f"gui/{os.getuid()}"
    stop_launch_agent(domain)
    temporary_root = Path(
        subprocess.run(
            ["/usr/bin/getconf", "DARWIN_USER_TEMP_DIR"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        ).stdout.strip()
    )
    remove_abandoned_generations(temporary_root)
    bootstrap_launch_agent(domain, plist_path)


if __name__ == "__main__":
    restart_agenix_launch_agent(Path(sys.argv[1]))
