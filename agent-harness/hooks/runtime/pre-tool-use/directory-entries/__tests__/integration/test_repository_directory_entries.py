import json
import subprocess

import pytest

from directory_entry_policy import (
    created_entry_violations,
    directory_entry_counts,
    directory_entry_violations,
)
from repository_directory_entries import (
    BASELINE_RELATIVE_PATH,
    directory_entry_ceilings,
    repository_entry_counts,
    repository_root_for_path,
)


@pytest.fixture
def repository(tmp_path):
    repository_root = tmp_path / "repository"
    repository_root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repository_root)], check=True)
    return repository_root


def test_counts_immediate_files_and_directories_together():
    paths = [f"source/file{index}.py" for index in range(14)]
    paths += ["source/nested/a.py", "source/nested/b.py"]
    counts = directory_entry_counts(paths)
    assert counts == {".": 1, "source": 15, "source/nested": 2}
    assert directory_entry_violations(counts, {}) == []
    paths.append("source/sixteenth.md")
    violation = directory_entry_violations(directory_entry_counts(paths), {})[0]
    assert (violation.directory, violation.count, violation.ceiling) == (
        "source",
        16,
        15,
    )


def test_creation_checks_only_directories_that_gain_an_entry():
    existing = [f"crowded/file{index}.py" for index in range(16)]
    existing.append("crowded/module/a.py")
    assert created_entry_violations(existing, ["crowded/module/b.py"], {}) == []
    violation = created_entry_violations(existing, ["crowded/new.py"], {})[0]
    assert (violation.directory, violation.count) == ("crowded", 18)


def test_git_scope_keeps_tracked_ignored_files_and_excludes_generated_files(repository):
    (repository / ".gitignore").write_text("generated/\ntracked.py\n")
    (repository / "tracked.py").write_text("pass\n")
    subprocess.run(["git", "add", "--force", "tracked.py"], cwd=repository, check=True)
    generated = repository / "generated"
    generated.mkdir()
    for index in range(20):
        (generated / f"file{index}.py").touch()
    (repository / "untracked.py").touch()
    (repository / "external-link").symlink_to(
        repository.parent, target_is_directory=True
    )
    assert repository_entry_counts(repository) == {".": 4}
    (repository / "tracked.py").unlink()
    assert repository_entry_counts(repository) == {".": 3}


def test_gitlink_counts_as_one_entry_without_scanning_its_contents(repository):
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            "160000," + "a" * 40 + ",dependency",
        ],
        cwd=repository,
        check=True,
    )
    dependency = repository / "dependency"
    dependency.mkdir()
    for index in range(20):
        (dependency / f"file{index}.py").touch()
    assert repository_entry_counts(repository) == {".": 1}


def test_repository_discovery_handles_new_parents_and_non_repositories(
    repository, tmp_path
):
    assert repository_root_for_path(repository / "new/nested/file.py") == repository
    assert repository_root_for_path(tmp_path / "outside" / "file.py") is None


def test_baseline_permits_existing_size_but_blocks_growth(repository):
    baseline = repository / BASELINE_RELATIVE_PATH
    baseline.parent.mkdir(parents=True)
    baseline.write_text(json.dumps({"legacy": 20}))
    ceilings = directory_entry_ceilings(repository)
    assert directory_entry_violations({"legacy": 20}, ceilings) == []
    violation = directory_entry_violations({"legacy": 21}, ceilings)[0]
    assert violation.ceiling == 20
    assert len(directory_entry_violations({"other": 16}, ceilings)) == 1


@pytest.mark.parametrize("invalid", [{"legacy": True}, {"legacy": 15}, []])
def test_invalid_baseline_is_rejected(repository, invalid):
    baseline = repository / BASELINE_RELATIVE_PATH
    baseline.parent.mkdir(parents=True)
    baseline.write_text(json.dumps(invalid))
    with pytest.raises(ValueError):
        directory_entry_ceilings(repository)


def test_missing_baseline_uses_hard_limit(repository):
    assert directory_entry_ceilings(repository) == {}
