import hashlib
from pathlib import Path
import re
import tomllib

import pytest


HERDR_DIRECTORY = Path(__file__).resolve().parents[2]
PACKAGE_IDENTITIES = {
    "herdr-agent-resume": {
        "recipe_path": "herdr-agent-resume-package.nix",
        "lock_hash": "5f3403ac35f92c840a38e7f46abbd70617fa6f5ddc3c62cde60d758331e9cbea",
    },
    "herdr-annotate": {
        "recipe_path": "annotation/herdr-annotate-package.nix",
        "lock_hash": "01024d372dd6770e31d58bca8d3468c0756f8f8c7bcb20b56f4d6a9c58d5017d",
    },
}


def package_recipe(package_name):
    return HERDR_DIRECTORY / PACKAGE_IDENTITIES[package_name]["recipe_path"]


def local_cargo_lock(package_name):
    recipe_path = package_recipe(package_name)
    recipe = recipe_path.read_text()
    assignment = re.search(r"cargoLock\.lockFile\s*=\s*(\.\.?/[^\s;]+)\s*;", recipe)
    assert assignment, (
        "Cargo lock must be a local source path without derivation context"
    )
    lock = recipe_path.parent / assignment.group(1)
    assert lock.is_file(), "Declared local Cargo lock must exist in repository source"
    return lock


@pytest.mark.parametrize("package_name", PACKAGE_IDENTITIES)
def test_cargo_lock_can_be_read_without_realizing_upstream_source(package_name):
    lock = local_cargo_lock(package_name)
    manifest = tomllib.loads(lock.read_text())
    assert manifest["version"] == 4
    assert any(package["name"] == package_name for package in manifest["package"])


@pytest.mark.parametrize("package_name,identity", PACKAGE_IDENTITIES.items())
def test_local_lock_preserves_exact_pinned_upstream_dependencies(
    package_name, identity
):
    lock = local_cargo_lock(package_name)
    assert hashlib.sha256(lock.read_bytes()).hexdigest() == identity["lock_hash"]
