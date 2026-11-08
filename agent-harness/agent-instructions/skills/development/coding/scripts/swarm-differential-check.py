import argparse
import difflib
import shlex
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

FILES_PLACEHOLDER = "{files}"
ROOT_PLACEHOLDER = "<root>"
DIFF_LINE_LIMIT = 40
STDERR_TAIL_LINE_COUNT = 10


@dataclass(frozen=True)
class CommandObservation:
    exit_status: str
    stdout: str
    stderr_tail: str = field(default="", compare=False)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="swarm-differential-check",
        description="Run the same commands in a snapshot of a git revision and in the working tree, and report any command whose exit status or stdout differs.",
    )
    parser.add_argument(
        "--check",
        action="append",
        required=True,
        help="Shell command run from each root; {files} expands to the quoted files modified since --revision. Repeatable.",
    )
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Pathspec limiting which modified files {files} expands to. Repeatable.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600)
    return parser.parse_args()


def git_output(repository, *arguments):
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        check=True,
        timeout=300,
    ).stdout


def files_modified_since_revision(repository, revision, pathspecs):
    listing = git_output(
        repository,
        "diff",
        "--name-only",
        "--diff-filter=M",
        revision,
        "--",
        *pathspecs,
    )
    return listing.decode().splitlines()


def extract_revision_snapshot(repository, revision, snapshot_root):
    with subprocess.Popen(
        ["git", "-C", str(repository), "archive", "--format=tar", revision],
        stdout=subprocess.PIPE,
    ) as archive_process:
        with tarfile.open(fileobj=archive_process.stdout, mode="r|") as snapshot:
            snapshot.extractall(snapshot_root, filter="tar")
        if archive_process.wait(timeout=300) != 0:
            raise SystemExit(f"git archive {revision} failed")


def repository_top_level(directory):
    return Path(git_output(directory, "rev-parse", "--show-toplevel").decode().strip())


def command_with_files(check_command, files):
    return check_command.replace(
        FILES_PLACEHOLDER, " ".join(shlex.quote(file) for file in files)
    )


def observe_command(command, root, timeout_seconds):
    try:
        completed = subprocess.run(
            ["bash", "-c", command],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return CommandObservation(f"timed out after {timeout_seconds}s", "")
    return CommandObservation(
        f"exit {completed.returncode}",
        completed.stdout.replace(str(root), ROOT_PLACEHOLDER),
        "\n".join(completed.stderr.strip().splitlines()[-STDERR_TAIL_LINE_COUNT:]),
    )


def stderr_tail_lines(revision, original, edited):
    return [
        line
        for label, observation in ((revision, original), ("working tree", edited))
        if observation.stderr_tail
        for line in [
            f"  stderr at {label}:",
            *(f"    {tail}" for tail in observation.stderr_tail.splitlines()),
        ]
    ]


def stdout_diff_lines(revision, original, edited):
    stdout_diff = difflib.unified_diff(
        original.stdout.splitlines(),
        edited.stdout.splitlines(),
        fromfile=f"stdout at {revision}",
        tofile="stdout in working tree",
        lineterm="",
    )
    return [f"  {line}" for line in stdout_diff][:DIFF_LINE_LIMIT]


def describe_difference(revision, original, edited):
    return "\n".join(
        [
            f"  {revision}: {original.exit_status}, working tree: {edited.exit_status}",
            *stderr_tail_lines(revision, original, edited),
            *stdout_diff_lines(revision, original, edited),
        ]
    )


def compare_check(check_command, files, roots, arguments):
    command = command_with_files(check_command, files)
    original, edited = (
        observe_command(command, root, arguments.timeout_seconds) for root in roots
    )
    if original == edited:
        print(f"SAME     {check_command}")
        return True
    print(f"DIFFERS  {check_command}")
    print(describe_difference(arguments.revision, original, edited))
    return False


def main():
    arguments = parse_arguments()
    repository = repository_top_level(arguments.repository.resolve())
    files = files_modified_since_revision(
        repository, arguments.revision, arguments.path
    )
    print(f"{len(files)} files modified since {arguments.revision}")
    with tempfile.TemporaryDirectory(prefix="swarm-differential-") as snapshot_root:
        extract_revision_snapshot(repository, arguments.revision, snapshot_root)
        roots = (Path(snapshot_root).resolve(), repository)
        results = [
            compare_check(check_command, files, roots, arguments)
            for check_command in arguments.check
        ]
    print(f"{sum(results)} of {len(results)} checks behave identically")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
