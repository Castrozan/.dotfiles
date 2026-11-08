import subprocess

import pytest
from orchestration_test_support import run_orchestrator
from orchestrator_cli.user_model import cli as user_model_cli

MODEL_PATH = "agent-harness/user-model/USER.md"
FIRST_DIRECTIVE = (
    "- U-001 · active · 2026-11-08 · scope: merges · "
    "Never merge without review · source: stated\n"
)
SECOND_DIRECTIVE = (
    "- U-002 · active · 2026-11-08 · scope: tickets · "
    "Never take an unassigned ticket · source: stated\n"
)
ISOLATED_GIT_CONFIGURATION = {
    "core.hooksPath": "/dev/null",
    "commit.gpgsign": "false",
    "user.name": "t",
    "user.email": "t@t",
    "protocol.file.allow": "always",
    "init.defaultBranch": "main",
}
NEW_DIRECTIVE = [
    "add",
    "--kind",
    "Prefer",
    "--scope",
    "retirement",
    "--rule",
    "porting only what was named",
    "--source",
    "D-20261108-179e38",
]


def git(repository, *arguments):
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return completed.stdout.strip()


def commit_model(checkout, text):
    model = checkout / MODEL_PATH
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_text(text)
    git(checkout, "add", MODEL_PATH)
    git(checkout, "commit", "-qm", "model")
    git(checkout, "push", "-q", "origin", "HEAD:main")


@pytest.fixture
def repositories(monkeypatch, tmp_path):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_COUNT", str(len(ISOLATED_GIT_CONFIGURATION)))
    for index, (key, value) in enumerate(ISOLATED_GIT_CONFIGURATION.items()):
        monkeypatch.setenv(f"GIT_CONFIG_KEY_{index}", key)
        monkeypatch.setenv(f"GIT_CONFIG_VALUE_{index}", value)
    origin = tmp_path / "origin.git"
    other_machine = tmp_path / "other-machine"
    superproject = tmp_path / "superproject"
    git(tmp_path, "init", "-q", "--bare", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(other_machine))
    commit_model(other_machine, "# USER\n\n" + FIRST_DIRECTIVE)
    superproject.mkdir()
    git(superproject, "init", "-q")
    git(superproject, "submodule", "add", "-q", str(origin), "private")
    git(superproject, "commit", "-qm", "pin")
    submodule = superproject / "private"
    git(submodule, "checkout", "-q", "--detach")
    model = submodule / MODEL_PATH
    monkeypatch.setattr(user_model_cli, "default_user_model_path", lambda: model)
    return origin, other_machine, superproject, submodule, model


def add_directive(monkeypatch, model):
    return run_orchestrator(
        monkeypatch, model, *NEW_DIRECTIVE, command="user", location_flag="--file"
    )


def test_a_learned_directive_reaches_origin_this_checkout_and_the_pinned_gitlink(
    monkeypatch, repositories, capsys
):
    origin, other_machine, superproject, submodule, model = repositories
    commit_model(other_machine, model.read_text() + SECOND_DIRECTIVE)
    (superproject / "peer.txt").write_text("staged by a peer\n")
    git(superproject, "add", "peer.txt")
    assert add_directive(monkeypatch, model) == 0
    assert capsys.readouterr().out.strip() == "U-003"
    published = git(origin, "show", f"main:{MODEL_PATH}")
    assert "U-002" in published and "U-003 · active" in published
    assert git(submodule, "rev-parse", "HEAD") == git(origin, "rev-parse", "main")
    pinned = git(superproject, "rev-parse", "HEAD:private")
    assert pinned == git(origin, "rev-parse", "main")
    assert "U-003 · active" in model.read_text()
    assert git(superproject, "status", "--short", "peer.txt") == "A  peer.txt"


def test_a_refused_push_leaves_nothing_half_written_and_a_retry_succeeds(
    monkeypatch, repositories, capsys
):
    origin, _, superproject, submodule, model = repositories
    pin_before = git(superproject, "rev-parse", "HEAD:private")
    git(submodule, "remote", "set-url", "--push", "origin", "/nonexistent/origin")
    assert add_directive(monkeypatch, model) == 1
    assert "U-002" not in model.read_text()
    assert git(superproject, "rev-parse", "HEAD:private") == pin_before
    assert "orchestrator user:" in capsys.readouterr().err
    git(submodule, "remote", "set-url", "--push", "origin", str(origin))
    assert add_directive(monkeypatch, model) == 0
    assert "U-002 · active" in git(origin, "show", f"main:{MODEL_PATH}")
