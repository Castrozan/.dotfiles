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
