from pathlib import Path

import pytest

from cycle_commands import CommandResult
from cycle_repository import Repository, RepositoryStateUnknown


class ScriptedRunner:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def run(self, arguments, directory, timeout_seconds):
        git_arguments = tuple(arguments[3:])
        self.calls.append(git_arguments)
        for prefix, result in self.responses:
            if git_arguments[: len(prefix)] == prefix:
                return result
        return CommandResult(1, "", "unscripted")


def repository_answering(*responses, path=Path("/repository")):
    runner = ScriptedRunner(list(responses))
    return Repository(path, runner), runner


def test_dirty_paths_keep_a_leading_status_space_and_skip_rename_sources():
    porcelain = " M machine/a.nix\0R  machine/new.nix\0machine/old.nix\0M  b.py\0"
    repository, _ = repository_answering((("status",), CommandResult(0, porcelain)))

    assert repository.tracked_dirty_paths() == [
        "machine/a.nix",
        "machine/new.nix",
        "b.py",
    ]


def test_divergence_that_cannot_be_counted_is_an_error_not_zero():
    repository, _ = repository_answering(
        (("rev-list",), CommandResult(128, "", "fatal: bad revision"))
    )

    with pytest.raises(RepositoryStateUnknown):
        repository.divergence()


def test_divergence_reads_behind_then_ahead():
    repository, _ = repository_answering((("rev-list",), CommandResult(0, "3\t2\n")))

    assert repository.divergence() == (3, 2)


def test_unresolvable_reference_is_an_error():
    repository, _ = repository_answering((("rev-parse",), CommandResult(1, "")))

    with pytest.raises(RepositoryStateUnknown):
        repository.revision("origin/main")


def test_rebase_that_stops_on_a_conflict_is_aborted(tmp_path):
    (tmp_path / "rebase-merge").mkdir()
    repository, runner = repository_answering(
        (("rebase", "--quiet"), CommandResult(1, "", "CONFLICT")),
        (("rev-parse", "--absolute-git-dir"), CommandResult(0, str(tmp_path))),
        (("rebase", "--abort"), CommandResult(0, "")),
    )

    assert repository.rebase_onto_upstream() == "conflict"
    assert ("rebase", "--abort") in runner.calls


def test_rebase_refused_without_leaving_a_rebase_is_a_plain_failure(tmp_path):
    repository, runner = repository_answering(
        (
            ("rebase", "--quiet"),
            CommandResult(1, "", "cannot rebase: You have unstaged changes"),
        ),
        (("rev-parse", "--absolute-git-dir"), CommandResult(0, str(tmp_path))),
    )

    assert repository.rebase_onto_upstream() == "failed"
    assert ("rebase", "--abort") not in runner.calls


def test_push_only_fast_forwards_the_named_revision():
    repository, runner = repository_answering((("push",), CommandResult(0, "")))

    assert repository.push("c" * 40).succeeded
    assert runner.calls == [
        ("push", "--quiet", "origin", f"{'c' * 40}:refs/heads/main")
    ]


def test_oldest_unvalidated_commit_time_spans_the_range_after_the_last_green(tmp_path):
    repository, _ = repository_answering(
        (("merge-base", "--is-ancestor"), CommandResult(0, "")),
        (("log", "--format=%ct"), CommandResult(0, "300\n100\n200\n")),
    )

    assert repository.oldest_commit_time_since("g" * 40, "h" * 40) == 100


def test_unpublished_submodule_pin_is_reported(tmp_path):
    submodule = tmp_path / "private-configuration"
    (submodule / ".git").mkdir(parents=True)
    repository, _ = repository_answering(
        (
            ("config", "--file"),
            CommandResult(
                0, "submodule.private-configuration.path private-configuration\n"
            ),
        ),
        (
            ("rev-parse", f"{'h' * 40}:private-configuration"),
            CommandResult(0, "p" * 40),
        ),
        (("fetch",), CommandResult(0, "")),
        (("branch", "--remotes", "--contains"), CommandResult(0, "")),
        path=tmp_path,
    )

    assert repository.unpublished_submodule_pins("h" * 40) == [
        f"private-configuration@{'p' * 40}"
    ]


def test_without_any_green_revision_every_commit_counts_as_unvalidated():
    repository, runner = repository_answering()

    assert repository.oldest_commit_time_since(None, "h" * 40) == 0
    assert runner.calls == []
