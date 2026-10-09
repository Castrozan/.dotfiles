from pathlib import Path


def write_native_library_fixture(directory):
    library = directory / "nixos_rebuild"
    library.mkdir()
    (library / "models.py").write_text(
        """from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class NixOSRebuildError(Exception):
    pass

class Action(Enum):
    SWITCH = "switch"
    BOOT = "boot"

@dataclass
class Profile:
    name: str
    @classmethod
    def from_arg(cls, name):
        return cls(name)

@dataclass
class Flake:
    path: str
    attr: str
    @classmethod
    def parse(cls, reference):
        path, attribute = reference.split("#", 1)
        return cls(path, f'nixosConfigurations."{attribute}"')
    def to_attr(self, *attributes):
        return self.path + "#" + self.attr + "." + ".".join(attributes)
"""
    )
    (library / "__init__.py").write_text(
        """import argparse
from types import SimpleNamespace

def parse_args(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--flake")
    parser.add_argument("--profile-name", default="system")
    parser.add_argument("--specialisation")
    parser.add_argument("--max-jobs")
    parser.add_argument("--cores")
    parser.add_argument("--option", nargs=2, action="append")
    parser.add_argument("--override-input", nargs=2, action="append")
    parser.add_argument("--build-host")
    parser.add_argument("--target-host")
    parser.add_argument("--file")
    parser.add_argument("--attr")
    parser.add_argument("--include", action="append")
    for name in ("impure", "rollback", "upgrade", "upgrade-all", "commit-lock-file", "recreate-lock-file", "refresh", "show-trace", "no-write-lock-file", "install-bootloader", "sudo", "no-reexec"):
        parser.add_argument("--" + name, action="store_true")
    parser.add_argument("--ask-sudo-password", action="store_true")
    parser.add_argument("--update-input", action="append")
    parsed = parser.parse_args(arguments[1:])
    common = {name: getattr(parsed, name) for name in ("option", "cores", "max_jobs")}
    flake = {**common, "override_input": parsed.override_input, "no_write_lock_file": parsed.no_write_lock_file}
    grouped = SimpleNamespace(common_flags=common, build_flags=common, flake_common_flags=flake, flake_build_flags=flake)
    return parsed, grouped
"""
    )
    (library / "utils.py").write_text(
        """def dict_to_flags(values):
    arguments = []
    for name, value in values.items():
        if value is None or value is False or value == []:
            continue
        flag = "--" + name.replace("_", "-")
        if value is True:
            arguments.append(flag)
        elif isinstance(value, list):
            for item in value:
                arguments.append(flag)
                arguments.extend(item if isinstance(item, list) else [item])
        else:
            arguments.extend([flag, str(value)])
    return arguments
"""
    )
    (library / "nix.py").write_text(
        """import json
import os
import subprocess
import sys
from pathlib import Path
from .models import NixOSRebuildError

SWITCH_TO_CONFIGURATION_CMD_PREFIX = ["systemd-run"]

def record(event):
    with Path(os.environ["TEST_NATIVE_LOG"]).open("a") as events:
        events.write(json.dumps(event) + "\\n")

def set_profile(profile, path_to_config, target_host, sudo):
    assert target_host is None and sudo is False
    if os.environ.get("TEST_INVALID_SYSTEM") == "1":
        raise NixOSRebuildError("native validity check failed")
    if os.environ.get("TEST_PROFILE_FAILURE"):
        raise subprocess.CalledProcessError(int(os.environ["TEST_PROFILE_FAILURE"]), "nix-env")
    record({"phase": "profile", "profile": profile.name, "system": str(path_to_config)})

def switch_to_configuration(path_to_config, action, target_host, sudo, install_bootloader=False, specialisation=None):
    assert target_host is None and sudo is False
    assert SWITCH_TO_CONFIGURATION_CMD_PREFIX == []
    if os.environ.get("TEST_ACTIVATION_FAILURE"):
        raise subprocess.CalledProcessError(int(os.environ["TEST_ACTIVATION_FAILURE"]), "switch-to-configuration")
    if os.environ.get("TEST_ACTIVATION_HOLD") == "1":
        directory = Path(os.environ["TEST_PHASE_DIRECTORY"])
        (directory / "activation-pid").write_text(str(os.getpid()))
        worker = "import os, signal, time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); directory=Path(os.environ['TEST_PHASE_DIRECTORY']); (directory/'activation-descendant-started').touch(); " + "\\nwhile not (directory/'release-descendant').exists(): time.sleep(0.01)"
        subprocess.run([sys.executable, "-c", worker], close_fds=True)
    record({"phase": "activate", "action": action.value, "system": str(path_to_config), "install_bootloader": install_bootloader, "specialisation": specialisation})
"""
    )
    return Path(directory)
