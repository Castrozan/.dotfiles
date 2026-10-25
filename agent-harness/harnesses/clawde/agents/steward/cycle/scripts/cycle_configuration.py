import json
from dataclasses import dataclass
from pathlib import Path

QUIET_SECONDS = 15 * 60
STARVATION_SECONDS = 2 * 60 * 60
MAXIMUM_VALIDATION_ATTEMPTS = 3
UPSTREAM_REFERENCE = "origin/main"
UPSTREAM_BRANCH = "main"


@dataclass(frozen=True)
class CycleConfiguration:
    repository: Path
    entrypoint: Path
    configuration_attribute: str
    state_directory: Path
    idle_marker: Path
    inbox_directory: Path
    peers_file: Path
    nix_binary: str
    rebuild_command: str
    dry_run: bool

    @property
    def validations_directory(self) -> Path:
        return self.state_directory / "validations"

    @property
    def activations_directory(self) -> Path:
        return self.state_directory / "activations"

    @property
    def continuous_integration_directory(self) -> Path:
        return self.state_directory / "continuous-integration"

    @property
    def attention_file(self) -> Path:
        return self.state_directory / "attention.json"

    @property
    def decision_file(self) -> Path:
        return self.state_directory / "decision.json"

    @property
    def rebase_conflict_file(self) -> Path:
        return self.state_directory / "rebase-conflict.json"

    @property
    def last_green_file(self) -> Path:
        return self.state_directory / "last-green-revision"

    @property
    def synchronization_pending_file(self) -> Path:
        return self.state_directory / "synchronization-pending-since"

    @property
    def lock_file(self) -> Path:
        return self.state_directory / "cycle.lock"

    def pinned_repository_reference(self, revision: str) -> str:
        return f"git+file://{self.repository}?submodules=1&rev={revision}"

    def entrypoint_installable(self, entrypoint_revision: str) -> str:
        return (
            f"git+file://{self.entrypoint}?rev={entrypoint_revision}"
            f"#{self.configuration_attribute}"
        )

    @classmethod
    def from_settings(
        cls, settings_path: Path, runtime_directory: Path, dry_run: bool
    ) -> "CycleConfiguration":
        settings = json.loads(settings_path.read_text())
        return cls(
            repository=Path(settings["repository"]),
            entrypoint=Path(settings["entrypoint"]),
            configuration_attribute=settings["configuration_attribute"],
            state_directory=Path(settings["state_directory"]),
            idle_marker=runtime_directory / settings["idle_marker_name"],
            inbox_directory=Path(settings["inbox_directory"]),
            peers_file=Path(settings["peers_file"]),
            nix_binary=settings["nix_binary"],
            rebuild_command=settings["rebuild_command"],
            dry_run=dry_run,
        )
