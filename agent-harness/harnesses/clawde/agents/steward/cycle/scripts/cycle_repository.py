from pathlib import Path

from cycle_commands import CommandResult, CommandRunner
from cycle_configuration import UPSTREAM_BRANCH, UPSTREAM_REFERENCE

GIT_TIMEOUT_SECONDS = 30
NETWORK_TIMEOUT_SECONDS = 60
REBASE_TIMEOUT_SECONDS = 120
OPERATION_MARKERS = (
    "rebase-merge",
    "rebase-apply",
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
)


class RepositoryStateUnknown(RuntimeError):
    pass


class Repository:
    def __init__(self, path: Path, runner: CommandRunner):
        self.path = path
        self.runner = runner

    def git(
        self, *arguments: str, timeout_seconds: int = GIT_TIMEOUT_SECONDS
    ) -> CommandResult:
        return self.runner.run(
            ["git", "-C", str(self.path), *arguments], self.path, timeout_seconds
        )

    def output(self, *arguments: str) -> str:
        result = self.git(*arguments)
        return result.output if result.succeeded else ""

    def fetch(self) -> bool:
        return self.git(
            "fetch",
            "--quiet",
            "origin",
            UPSTREAM_BRANCH,
            timeout_seconds=NETWORK_TIMEOUT_SECONDS,
        ).succeeded

    def current_branch(self) -> str:
        return self.output("symbolic-ref", "--quiet", "--short", "HEAD")

    def revision(self, reference: str) -> str:
        resolved = self.output(
            "rev-parse", "--verify", "--quiet", f"{reference}^{{commit}}"
        )
        if not resolved:
            raise RepositoryStateUnknown(f"cannot resolve {reference} in {self.path}")
        return resolved

    def divergence(self) -> tuple[int, int]:
        counts = self.output(
            "rev-list", "--left-right", "--count", f"{UPSTREAM_REFERENCE}...HEAD"
        ).split()
        if len(counts) != 2 or not all(count.isdigit() for count in counts):
            raise RepositoryStateUnknown(
                f"cannot count divergence from {UPSTREAM_REFERENCE}"
            )
        return int(counts[0]), int(counts[1])

    def commit_time(self, revision: str) -> int:
        text = self.output("show", "-s", "--format=%ct", revision)
        return int(text) if text.isdigit() else 0

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        return self.git("merge-base", "--is-ancestor", ancestor, descendant).succeeded

    def oldest_commit_time_since(self, base: str, head: str) -> int:
        if not base:
            return 0
        if self.is_ancestor(base, head):
            times = [
                int(text)
                for text in self.output(
                    "log", "--format=%ct", f"{base}..{head}"
                ).split()
                if text.isdigit()
            ]
            if times:
                return min(times)
        return self.commit_time(head)

    def operation_in_progress(self) -> bool:
        git_directory = self.output("rev-parse", "--absolute-git-dir")
        if not git_directory:
            raise RepositoryStateUnknown(
                f"cannot locate the git directory of {self.path}"
            )
        return any(
            (Path(git_directory) / marker).exists() for marker in OPERATION_MARKERS
        )

    def tracked_dirty_paths(self) -> list[str]:
        entries = [
            entry
            for entry in self.git(
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=no",
                "--ignore-submodules=dirty",
            ).stdout.split("\0")
            if entry
        ]
        paths = []
        skip_next = False
        for entry in entries:
            if skip_next:
                skip_next = False
                continue
            paths.append(entry[3:])
            skip_next = entry[0] in "RC"
        return paths

    def newest_modification_time(self, relative_paths: list[str]) -> float:
        existing = [
            self.path / relative
            for relative in relative_paths
            if (self.path / relative).exists()
        ]
        return max((path.stat().st_mtime for path in existing), default=0.0)

    def is_clean(self) -> bool:
        result = self.git("status", "--porcelain=v1", "--untracked-files=no")
        return result.succeeded and not result.output

    def merge_fast_forward(self) -> CommandResult:
        return self.git("merge", "--ff-only", "--quiet", UPSTREAM_REFERENCE)

    def update_submodules(self) -> CommandResult:
        return self.git(
            "submodule",
            "update",
            "--init",
            "--recursive",
            timeout_seconds=NETWORK_TIMEOUT_SECONDS,
        )

    def rebase_onto_upstream(self) -> str:
        if self.git(
            "rebase",
            "--quiet",
            UPSTREAM_REFERENCE,
            timeout_seconds=REBASE_TIMEOUT_SECONDS,
        ).succeeded:
            return "rebased"
        if self.operation_in_progress():
            self.git("rebase", "--abort")
            return "conflict"
        return "failed"

    def push(self, revision: str) -> CommandResult:
        return self.git(
            "push",
            "--quiet",
            "origin",
            f"{revision}:refs/heads/{UPSTREAM_BRANCH}",
            timeout_seconds=NETWORK_TIMEOUT_SECONDS,
        )

    def submodule_paths(self) -> list[str]:
        lines = self.output(
            "config", "--file", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"
        ).splitlines()
        return [line.split(" ", 1)[1] for line in lines if " " in line]

    def unpublished_submodule_pins(self, revision: str) -> list[str]:
        unpublished = []
        for submodule_path in self.submodule_paths():
            pin = self.output("rev-parse", f"{revision}:{submodule_path}")
            submodule = Repository(self.path / submodule_path, self.runner)
            if not pin or not (submodule.path / ".git").exists():
                continue
            submodule.git(
                "fetch", "--quiet", "origin", timeout_seconds=NETWORK_TIMEOUT_SECONDS
            )
            if not submodule.output("branch", "--remotes", "--contains", pin):
                unpublished.append(f"{submodule_path}@{pin}")
        return unpublished
