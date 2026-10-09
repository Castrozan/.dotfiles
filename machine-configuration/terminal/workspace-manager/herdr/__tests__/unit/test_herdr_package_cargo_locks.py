import hashlib
from pathlib import Path
import re
import tomllib

import pytest


HERDR_DIRECTORY = Path(__file__).resolve().parents[2]
PACKAGE_IDENTITIES = {
    "herdr-agent-resume": {
        "owner": "Angel-O",
        "revision": "dcd6417ac87b5d73e8b32e12486a4838850e8b1a",
        "source_hash": "sha256-TClh+l0+2XT04NLQD9ZEq1cny1LuSENyxDLy62OKEaQ=",
        "lock_hash": "5f3403ac35f92c840a38e7f46abbd70617fa6f5ddc3c62cde60d758331e9cbea",
    },
    "herdr-annotate": {
        "owner": "plannotator",
        "revision": "663b45a420f00882f7196bf893b341cddd37a530",
        "source_hash": "sha256-MLHF21wqghawj3rk+UsyFdaGqIgVYXVG7UH2H+q0/lE=",
        "lock_hash": "01024d372dd6770e31d58bca8d3468c0756f8f8c7bcb20b56f4d6a9c58d5017d",
    },
}


def local_cargo_lock(package_name):
    recipe = (HERDR_DIRECTORY / (package_name + "-package.nix")).read_text()
    assignment = re.search(r"cargoLock\.lockFile\s*=\s*(\./[^\s;]+)\s*;", recipe)
    assert assignment, (
        "Cargo lock must be a local source path without derivation context"
    )
    lock = HERDR_DIRECTORY / assignment.group(1).removeprefix("./")
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


@pytest.mark.parametrize("package_name,identity", PACKAGE_IDENTITIES.items())
def test_local_lock_remains_bound_to_declared_upstream_pin(package_name, identity):
    recipe = (HERDR_DIRECTORY / (package_name + "-package.nix")).read_text()
    source = recipe.split("pkgs.fetchFromGitHub", 1)[1].split("\n  };", 1)[0]
    assert re.search(r'\bowner\s*=\s*"' + identity["owner"] + '";', source)
    assert re.search(r'\brepo\s*=\s*"' + package_name + '";', source)
    assert re.search(r'\brev\s*=\s*"' + identity["revision"] + '";', source)
    assert re.search(
        r'\bhash\s*=\s*"' + re.escape(identity["source_hash"]) + '";', source
    )
