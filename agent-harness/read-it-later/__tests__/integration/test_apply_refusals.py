import pytest

from application.apply import ApplyRefused, apply_pull_request
from group_scenarios import request_for


def test_the_watchers_own_comment_is_never_an_approval(
    repository_with_origin,
    sandbox_vault,
    recording_forge,
    recording_launcher,
    proposed_group,
):
    _, inbox = proposed_group
    own = recording_forge.comment(1, "looks good\n\n<!-- ril-watcher -->")

    with pytest.raises(ApplyRefused):
        apply_pull_request(
            request_for(
                repository_with_origin,
                sandbox_vault,
                inbox,
                recording_forge,
                recording_launcher,
                own,
            )
        )
    assert recording_forge.pull_request(1)["state"] == "OPEN"


def test_an_entry_with_a_tag_outside_the_legend_fails_and_frees_its_capture(
    repository_with_origin,
    sandbox_vault,
    recording_forge,
    recording_launcher,
    proposed_group,
):
    _, inbox = proposed_group
    (sandbox_vault / "Second Brain" / "Atlas" / "Tag Legend.md").write_text(
        "# Tag Legend\n"
    )
    approval = recording_forge.comment(1, "approved", "2026-11-08T13:00:00Z")

    report = apply_pull_request(
        request_for(
            repository_with_origin,
            sandbox_vault,
            inbox,
            recording_forge,
            recording_launcher,
            approval,
        )
    )

    failed = [result for result in report["results"] if result["status"] == "failed"]
    assert len(failed) == 1 and "Tag Legend" in failed[0]["reason"]
    assert report["merge"] == "not-merged"
    assert "status:: working" not in (inbox / failed[0]["capture"]).read_text()


def test_a_closed_group_is_refused_before_any_card_runs(
    repository_with_origin,
    sandbox_vault,
    recording_forge,
    recording_launcher,
    proposed_group,
):
    _, inbox = proposed_group
    approval = recording_forge.comment(1, "approved", "2026-11-08T13:00:00Z")
    recording_forge.pull_request(1)["state"] = "CLOSED"

    with pytest.raises(ApplyRefused, match="CLOSED"):
        apply_pull_request(
            request_for(
                repository_with_origin,
                sandbox_vault,
                inbox,
                recording_forge,
                recording_launcher,
                approval,
            )
        )
    assert recording_launcher.launches == []


def test_a_capture_deleted_from_the_inbox_is_skipped_and_does_not_block_the_merge(
    repository_with_origin,
    sandbox_vault,
    recording_forge,
    recording_launcher,
    proposed_group,
):
    group, inbox = proposed_group
    (inbox / group["cards"][1]["capture"]).unlink()
    approval = recording_forge.comment(1, "approved", "2026-11-08T13:00:00Z")

    report = apply_pull_request(
        request_for(
            repository_with_origin,
            sandbox_vault,
            inbox,
            recording_forge,
            recording_launcher,
            approval,
        )
    )

    assert {"capture": group["cards"][1]["capture"], "status": "missing"} in report[
        "results"
    ]
    assert report["merge"] == "merged"
