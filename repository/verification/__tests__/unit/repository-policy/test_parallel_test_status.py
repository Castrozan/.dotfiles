import itertools
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

REPOSITORY = Path(__file__).resolve().parents[5]
WORKFLOW = REPOSITORY / ".github/workflows/tests.yml"
PRODUCERS = ("swift-tests", "python-tests", "qml-tests", "bash-coverage")
RESULTS = ("success", "failure", "cancelled", "skipped")


def test_language_execution_is_independent_and_required_status_joins_all_producers():
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    gate = jobs["qml-and-python-tests"]
    assert set(gate["needs"]) == set(PRODUCERS)
    assert gate["if"] == "${{ always() }}"
    assert all("needs" not in jobs[name] for name in PRODUCERS)
    python_workflow = yaml.safe_load(
        (REPOSITORY / jobs["python-tests"]["uses"]).read_text()
    )
    shards = python_workflow["jobs"]
    assert all("needs" not in shard for shard in shards.values())
    assert {
        (shard["with"]["tier"], shard["with"]["shard"], shard["with"]["count"])
        for shard in shards.values()
    } == {("unit", 0, 1), ("integration", 0, 2), ("integration", 1, 2)}
    assert len(shards) == 3
    assert len({shard["uses"] for shard in shards.values()}) == 1
    outputs = python_workflow[True]["workflow_call"]["outputs"]
    assert len(outputs) == 6
    downloads = [
        step
        for step in gate["steps"]
        if step.get("uses") == "actions/download-artifact@v4"
        and "artifact-ids" in step.get("with", {})
    ]
    assert len(downloads) == 3
    assert all(
        "name" not in step["with"] and "pattern" not in step["with"]
        for step in downloads
    )


@pytest.mark.parametrize("outcomes", itertools.product(RESULTS, repeat=len(PRODUCERS)))
def test_required_status_preserves_every_failed_skipped_and_cancelled_producer(
    outcomes,
):
    gate = yaml.safe_load(WORKFLOW.read_text())["jobs"]["qml-and-python-tests"]
    step = next(
        step
        for step in gate["steps"]
        if step.get("name") == "Require every test producer to succeed"
    )
    assert step["if"] == "${{ always() }}"
    results = dict(zip(PRODUCERS, outcomes, strict=True))
    environment = {
        name: results[expression.removeprefix("${{ needs.").removesuffix(".result }}")]
        for name, expression in step["env"].items()
    }
    process = subprocess.run(
        [shutil.which("bash"), "-e", "-c", step["run"]],
        env=environment,
        capture_output=True,
        timeout=5,
    )
    assert (process.returncode == 0) == all(
        outcome == "success" for outcome in outcomes
    )
