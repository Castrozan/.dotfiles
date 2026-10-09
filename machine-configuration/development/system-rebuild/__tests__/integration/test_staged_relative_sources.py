import json
import subprocess
import sys

import pytest

from staged_rebuild_support import PRIVATE_PATH, SOURCE_PATH, SCRIPTS
from test_staged_sources import prefetch_environment


@pytest.mark.parametrize("entrypoint", ["public", "private"])
def test_relative_inputs_share_parent_source_and_preserve_nested_archived_inputs(
    managed_rebuild_environment, tmp_path, entrypoint
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    environment["TEST_RELATIVE_INPUTS"] = "1"
    reference = (
        f"{tmp_path}/dotfiles?submodules=1#host"
        if entrypoint == "public"
        else f"git+file://{tmp_path}/private#chise"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "prefetch_rebuild.py"),
            str(tmp_path / "request.json"),
            str(tmp_path / "dotfiles"),
            "boot",
            "--flake",
            reference,
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    prepared = json.loads((tmp_path / "request.json").read_text())
    nested = "/nix/store/33333333333333333333333333333333-nested-source"
    expected = {SOURCE_PATH, nested}
    if entrypoint == "private":
        expected.add(PRIVATE_PATH)
    assert set(prepared["sources"]) == expected
    if entrypoint == "public":
        assert prepared["arguments"][-3:] == [
            "--override-input",
            "dependencies/nested",
            f"path:{nested}",
        ]
        assert "dependencies" not in prepared["arguments"]
