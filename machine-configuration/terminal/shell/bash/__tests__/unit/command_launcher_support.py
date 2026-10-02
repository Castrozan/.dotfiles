import os
import shlex
import shutil
import subprocess
from pathlib import Path

BASH_DIRECTORY = Path(__file__).resolve().parents[2]
LAUNCHER = BASH_DIRECTORY / "scripts/command-launcher/command-launcher.sh"
HISTORY = BASH_DIRECTORY / "program-configuration/bash_history.sh"
BASH = os.environ.get("SHELL", "")
if not Path(BASH).name.startswith("bash"):
    BASH = shutil.which("bash") or "/bin/bash"


def run_launcher(environment, commands):
    return subprocess.run(
        [
            BASH,
            "--noprofile",
            "--norc",
            "-c",
            f". {shlex.quote(str(HISTORY))}\n"
            f". {shlex.quote(str(LAUNCHER))}\n"
            "shopt -s expand_aliases\n"
            "launcher_scenario() {\n" + commands + "\n}\nlauncher_scenario",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
