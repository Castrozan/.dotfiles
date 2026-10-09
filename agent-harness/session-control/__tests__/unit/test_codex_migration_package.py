import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


SESSION_CONTROL = Path(__file__).resolve().parents[2]
RECIPE = SESSION_CONTROL / "codex-launcher-migration-package.nix"


def source_string(recipe, start):
    return recipe.split(start, 1)[1].split("''", 2)[1]


@pytest.fixture
def packaged_migration(tmp_path):
    python_package = tmp_path / "python-package"
    (python_package / "bin").mkdir(parents=True)
    (python_package / "bin/python3").symlink_to(sys.executable)
    scripts = tmp_path / "scripts"
    recipe = RECIPE.read_text()
    builder = source_string(recipe, "pkgs.runCommandLocal")

    def replacement(match):
        reference = match.group(1)
        if reference == "pkgs.python312":
            return str(python_package)
        if reference.startswith("./"):
            return str(SESSION_CONTROL / reference.removeprefix("./"))
        raise AssertionError(reference)

    builder = re.sub(r"\$\{([^}]+)\}", replacement, builder)
    built = subprocess.run(
        [shutil.which("bash"), "-euc", builder],
        env={**os.environ, "out": str(scripts)},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert built.returncode == 0, built.stderr
    wrapper = source_string(recipe, "pkgs.writeShellApplication")
    wrapper = wrapper.replace("${pkgs.python312}", str(python_package)).replace(
        "${migrationScripts}", str(scripts)
    )
    assert "${" not in wrapper
    return scripts, wrapper, tmp_path


def test_declared_package_layout_imports_without_checkout_or_pythonpath(
    packaged_migration,
):
    scripts, wrapper, directory = packaged_migration
    result = subprocess.run(
        [shutil.which("bash"), "-euc", wrapper, "fixture-wrapper", "--help"],
        cwd=directory,
        env={**os.environ, "PYTHONPATH": ""},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert "manifest attempt" in result.stdout
    assert sorted(str(path.relative_to(scripts)) for path in scripts.rglob("*.py")) == [
        "agent-session-codex-launcher-migration.py",
        "agent_session/codex_launcher_migration.py",
        "agent_session/codex_migration_connections.py",
        "agent_session/codex_migration_contract.py",
        "agent_session/codex_migration_inputs.py",
        "agent_session/codex_migration_journal.py",
        "agent_session/codex_migration_processes.py",
        "agent_session/codex_migration_readiness.py",
        "agent_session/codex_migration_terminal.py",
    ]
    assert not list(scripts.rglob("*.pyc"))


def test_declared_wrapper_ignores_inherited_python_import_configuration(
    packaged_migration,
):
    scripts, wrapper, directory = packaged_migration
    poison = directory / "inherited-imports/agent_session"
    poison.mkdir(parents=True)
    (poison / "__init__.py").write_text("raise SystemExit('untrusted module loaded')\n")
    result = subprocess.run(
        [shutil.which("bash"), "-euc", wrapper, "fixture-wrapper", "--help"],
        cwd=directory,
        env={**os.environ, "PYTHONPATH": str(poison.parent), "PYTHONHOME": str(poison)},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert "manifest attempt" in result.stdout
    assert not list(scripts.rglob("*.pyc"))


def test_packaged_driver_refuses_wrong_pane_before_runtime_commands(
    packaged_migration,
):
    scripts, wrapper, directory = packaged_migration
    plan = directory / "manifest.json"
    plan.write_text(
        json.dumps(
            {
                "pane_identifier": "fixture-other",
                "thread_identifier": "fixture-thread",
                "old_processes": [],
            }
        )
    )
    attempt = directory / "attempt"
    result = subprocess.run(
        [
            shutil.which("bash"),
            "-euc",
            wrapper,
            "fixture-wrapper",
            str(plan),
            str(attempt),
        ],
        cwd=directory,
        env={**os.environ, "HERDR_PANE_ID": "fixture-own"},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 1
    evidence = json.loads((attempt / "result.json").read_text())
    assert evidence["status"] == "failed"
    assert evidence["phase"] == "validate-declared-inputs"
    assert not list(attempt.glob("command-*"))
