import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContainerPolicy:
    workspace_root: str
    state_root: str
    image_directory: str
    virtual_machine: bool
    virtual_machine_profile: str
    virtual_machine_cpus: int
    virtual_machine_memory_gib: int
    virtual_machine_disk_gib: int
    container_cpus: int
    container_memory_bytes: int
    container_process_limit: int
    command_timeout_seconds: int
    session_timeout_seconds: int
    idle_timeout_seconds: int
    maximum_running_containers: int = 1

    @classmethod
    def load(cls, path):
        return cls(**json.loads(Path(path).read_text()))

    def project(self, directory):
        project = self.project_identity(directory)
        if not (project.directory / "devenv.nix").is_file():
            raise ValueError(f"No devenv.nix in {project.directory}")
        return project

    def project_identity(self, directory):
        project = Path(directory).resolve()
        root = Path(self.workspace_root).resolve()
        if project == root or not project.is_relative_to(root):
            raise ValueError(f"Choose a checkout beneath {root}")
        identity = hashlib.sha256(os.fsencode(project)).hexdigest()[:16]
        return ContainerProject(project, Path(self.state_root) / identity, identity)


@dataclass(frozen=True)
class ContainerProject:
    directory: Path
    state_directory: Path
    identity: str

    @property
    def name(self):
        return f"devenv-{self.identity}"

    @property
    def compose_path(self):
        return self.state_directory / "compose.json"


def compose_configuration(policy, project, git_metadata):
    workspace = str(project.directory).replace("$", "$$")
    volumes = {
        "home": "/home/devenv",
        "nix": "/nix",
        "dependencies": f"{workspace}/node_modules",
        "environment": f"{workspace}/.devenv",
        "output": f"{workspace}/dist",
    }
    return {
        "services": {
            "environment": {
                "build": {
                    "context": policy.image_directory,
                    "args": {
                        "workspace_uid": str(os.getuid()),
                        "workspace_gid": str(os.getgid()),
                        "workspace_directory": workspace,
                    },
                },
                "image": f"dotfiles-devenv:{os.getuid()}-{os.getgid()}-{project.identity}",
                "init": True,
                "restart": "no",
                "read_only": True,
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges:true"],
                "working_dir": workspace,
                "cpus": policy.container_cpus,
                "mem_limit": policy.container_memory_bytes,
                "memswap_limit": policy.container_memory_bytes,
                "pids_limit": policy.container_process_limit,
                "stop_grace_period": "10s",
                "environment": {
                    "DEVENV_CONTAINER_BIND_ADDRESS": "0.0.0.0",
                    "DEVENV_MAX_JOBS": "1",
                    "DEVENV_CORES": str(policy.container_cpus),
                    "NIX_CONFIG": f"max-jobs = 1\ncores = {policy.container_cpus}",
                },
                "command": [
                    "timeout",
                    "-k",
                    "10",
                    str(policy.session_timeout_seconds),
                    "sleep",
                    str(policy.session_timeout_seconds),
                ],
                "ports": ["127.0.0.1::8080"],
                "volumes": [
                    {"type": "bind", "source": workspace, "target": workspace},
                    *[
                        {
                            "type": "bind",
                            "source": str(path).replace("$", "$$"),
                            "target": str(path).replace("$", "$$"),
                        }
                        for path in git_metadata
                    ],
                    *[
                        {"type": "volume", "source": name, "target": target}
                        for name, target in volumes.items()
                    ],
                ],
                "tmpfs": ["/tmp:size=268435456,mode=1777"],
                "logging": {
                    "driver": "json-file",
                    "options": {"max-size": "5m", "max-file": "2"},
                },
            }
        },
        "volumes": {name: {} for name in volumes},
    }
