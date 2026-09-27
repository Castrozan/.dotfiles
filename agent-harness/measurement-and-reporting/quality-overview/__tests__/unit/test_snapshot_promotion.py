import json
from pathlib import Path

import pytest

import workflow_context as CONTEXT


def test_promotion_rejects_newer_main_and_rerun_attempt(run, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(CONTEXT.__file__).parent))
    import promote_snapshot

    payload = {"workflow": CONTEXT.workflow_identity(run)}
    assert promote_snapshot.promotion_matches(payload, run["head_sha"], run, run)
    assert not promote_snapshot.promotion_matches(payload, "b" * 40, run, run)
    assert not promote_snapshot.promotion_matches(
        payload, run["head_sha"], {**run, "run_attempt": 3}, run
    )


def test_stored_receipt_must_match_the_expected_report_location(
    run, tmp_path, monkeypatch
):
    monkeypatch.syspath_prepend(str(Path(CONTEXT.__file__).parent))
    import promote_snapshot

    expected = {"workflow": CONTEXT.workflow_identity(run)}
    foreign = {"workflow": CONTEXT.workflow_identity({**run, "id": 999})}
    monkeypatch.chdir(tmp_path)
    receipt_path = tmp_path / ".quality-results/overview/payload.json"
    context_path = tmp_path / ".quality-results/workflow-context.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(foreign))
    context_path.write_text(json.dumps(expected))
    monkeypatch.setattr(
        promote_snapshot,
        "github_document",
        lambda route: pytest.fail("Foreign receipt queried GitHub"),
    )
    with pytest.raises(ValueError, match="Stored receipt"):
        promote_snapshot.main()


@pytest.mark.parametrize("latest_attempt", [2, 3])
def test_promotion_uses_attempt_timestamp_and_rejects_newer_attempt(
    run, tmp_path, monkeypatch, capsys, latest_attempt
):
    monkeypatch.syspath_prepend(str(Path(CONTEXT.__file__).parent))
    import promote_snapshot

    payload = {"workflow": CONTEXT.workflow_identity(run)}
    latest = {
        **run,
        "run_attempt": latest_attempt,
        "updated_at": "2026-09-26T00:19:59Z",
    }
    route = f"repos/{CONTEXT.REPOSITORY}"
    responses = {
        f"{route}/commits/main": {"sha": run["head_sha"]},
        f"{route}/actions/runs/123": latest,
        f"{route}/actions/runs/123/attempts/2": run,
    }
    monkeypatch.chdir(tmp_path)
    output = tmp_path / ".quality-results/overview"
    output.mkdir(parents=True)
    (output / "payload.json").write_text(json.dumps(payload))
    (output.parent / "workflow-context.json").write_text(json.dumps(payload))
    monkeypatch.setattr(promote_snapshot, "github_document", responses.__getitem__)
    promote_snapshot.main()
    assert capsys.readouterr().out.strip() == (
        "true" if latest_attempt == 2 else "false"
    )
