import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

import fix_loop_check
import fix_loop_context
import fix_loop_deliver
import fix_loop_requests

TEST_COMMAND = f"{sys.executable} -B test_calculator.py"
DEFECT = "def add(first, second):\n    return first + second + 1\n"
FIXED = "def add(first, second):\n    return first + second\n"
GIT_TIMEOUT_SECONDS = 60


def git_command(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        capture_output=True,
        text=True,
        check=True,
        timeout=GIT_TIMEOUT_SECONDS,
    ).stdout


def git(directory: Path, *arguments: str) -> str:
    return git_command("-C", str(directory), *arguments)


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    configuration = tmp_path / "gitconfig"
    configuration.write_text(
        "[user]\n\tname = fixture\n\temail = fixture@example.invalid\n"
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(configuration))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.delenv("COVERAGE_PROCESS_START", raising=False)
    origin, root = tmp_path / "origin.git", tmp_path / "checkout"
    git_command("init", "-q", "--bare", "-b", "main", str(origin))
    git_command("init", "-q", "-b", "main", str(root))
    (root / "calculator.py").write_text(DEFECT)
    (root / "test_calculator.py").write_text(
        "from calculator import add\n\nassert add(2, 2) == 4, add(2, 2)\n"
    )
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "feat: add calculator")
    git(root, "remote", "add", "origin", str(origin))
    git(root, "push", "-q", "origin", "main")
    return root, origin, tmp_path / "artifacts"


def run_script(module, monkeypatch, capsys, *arguments: str) -> dict:
    monkeypatch.setattr(sys, "argv", [module.__name__, *arguments])
    module.main()
    return json.loads(capsys.readouterr().out)


def gather(monkeypatch, capsys, root: Path, artifacts: Path) -> dict:
    return run_script(
        fix_loop_context, monkeypatch, capsys,
        "--root", str(root), "--task", "add(2, 2) returns 5",
        "--test-command", TEST_COMMAND, "--artifacts", str(artifacts),
    )  # fmt: skip


def check(monkeypatch, capsys, root: Path, artifacts: Path) -> dict:
    return run_script(
        fix_loop_check, monkeypatch, capsys,
        "--root", str(root), "--test-command", TEST_COMMAND,
        "--lint-command", "", "--artifacts", str(artifacts),
    )  # fmt: skip


def deliver(monkeypatch, capsys, root: Path, answer: str) -> dict:
    return run_script(
        fix_loop_deliver, monkeypatch, capsys,
        "--root", str(root), "--answer", answer, "--test-command", TEST_COMMAND,
        "--commit-message", "fix(calculator): drop the stray one",
        "--upstream", "origin/main",
    )  # fmt: skip


def test_context_refuses_a_dirty_checkout_and_a_green_test(
    checkout, monkeypatch, capsys
):
    root, _, artifacts = checkout
    (root / "notes.txt").write_text("peer work in progress\n")
    with pytest.raises(SystemExit, match="uncommitted changes"):
        gather(monkeypatch, capsys, root, artifacts)
    (root / "notes.txt").unlink()
    (root / "calculator.py").write_text(FIXED)
    git(root, "commit", "-q", "-am", "fix: already fixed")
    with pytest.raises(SystemExit, match="already passes"):
        gather(monkeypatch, capsys, root, artifacts)


def test_an_unfixed_change_repeats_its_failure_and_forces_escalate(
    checkout, monkeypatch, capsys
):
    root, _, artifacts = checkout
    gather(monkeypatch, capsys, root, artifacts)
    first, second = (check(monkeypatch, capsys, root, artifacts) for _ in range(2))
    assert not first["passed"] and first["gates_passed"]
    assert first["failure_signature"] == second["failure_signature"] != ""
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(second)))
    request = run_script(
        fix_loop_requests, monkeypatch, capsys, "next", "--artifacts", str(artifacts),
        "--previous-signature", first["failure_signature"], "--max-iterations", "4",
    )  # fmt: skip
    assert [option["id"] for option in request["options"]] == ["escalate"]
    assert request["guarded"] is True


def test_a_broken_format_fails_the_gate_and_a_fix_passes(checkout, monkeypatch, capsys):
    root, _, artifacts = checkout
    gather(monkeypatch, capsys, root, artifacts)
    monkeypatch.setattr(
        fix_loop_check, "FORMATTERS", {".py": (sys.executable, "-m", "py_compile")}
    )
    (root / "calculator.py").write_text("def add(first, second:\n")
    broken = check(monkeypatch, capsys, root, artifacts)
    assert not broken["gates_passed"] and broken["changed_files"] == ["calculator.py"]
    (root / "calculator.py").write_text(FIXED)
    fixed = check(monkeypatch, capsys, root, artifacts)
    assert fixed["passed"] and fixed["failure_signature"] == ""
    assert "-    return first + second + 1" in (artifacts / "change.diff").read_text()


def test_a_committing_fixer_fails_the_gate(checkout, monkeypatch, capsys):
    root, _, artifacts = checkout
    gather(monkeypatch, capsys, root, artifacts)
    (root / "calculator.py").write_text(FIXED)
    git(root, "commit", "-q", "-am", "fix: the fixer committed")
    assert not check(monkeypatch, capsys, root, artifacts)["gates_passed"]


def test_a_held_answer_commits_and_pushes_nothing(checkout, monkeypatch, capsys):
    root, origin, _ = checkout
    (root / "calculator.py").write_text(FIXED)
    before = git(origin, "rev-parse", "main")
    assert deliver(monkeypatch, capsys, root, "escalate")["outcome"] == "held"
    assert git(origin, "rev-parse", "main") == before
    assert git(root, "status", "--porcelain") == " M calculator.py\n"


def test_a_merge_answer_commits_rebases_and_pushes(checkout, monkeypatch, capsys):
    root, origin, artifacts = checkout
    peer = artifacts.parent / "peer"
    git_command("clone", "-q", str(origin), str(peer))
    (peer / "README").write_text("peer commit\n")
    git(peer, "add", "README")
    git(peer, "commit", "-q", "-m", "docs: add readme")
    git(peer, "push", "-q", "origin", "main")
    (root / "calculator.py").write_text(FIXED)
    delivered = deliver(monkeypatch, capsys, root, "merge")
    assert (
        delivered["pushed"]
        and git(origin, "rev-parse", "main").strip() == (delivered["commit"])
    )
    assert git(origin, "log", "--format=%s", "-2", "main").splitlines() == [
        "fix(calculator): drop the stray one",
        "docs: add readme",
    ]


def test_a_conflicting_rebase_keeps_the_commit_local(checkout, monkeypatch, capsys):
    root, origin, artifacts = checkout
    peer = artifacts.parent / "peer"
    git_command("clone", "-q", str(origin), str(peer))
    (peer / "calculator.py").write_text("def add(first, second):\n    return 0\n")
    git(peer, "commit", "-q", "-am", "fix: a conflicting change")
    git(peer, "push", "-q", "origin", "main")
    pushed = git(origin, "rev-parse", "main")
    (root / "calculator.py").write_text(FIXED)
    with pytest.raises(SystemExit, match="conflicted"):
        deliver(monkeypatch, capsys, root, "merge")
    assert git(origin, "rev-parse", "main") == pushed
    assert not (root / ".git" / "rebase-merge").exists()
