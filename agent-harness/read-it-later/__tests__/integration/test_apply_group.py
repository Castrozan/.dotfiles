import copy

from application.apply import apply_pull_request
from group_scenarios import EXTENDED_AT, LUCAS_NOTE, request_for
from proposals.propose import ProposalContext, propose_groups


def test_an_approved_group_files_drops_launches_records_and_merges(
    repository_with_origin,
    sandbox_vault,
    recording_forge,
    recording_launcher,
    proposed_group,
):
    group, inbox = proposed_group
    approval = recording_forge.comment(1, "approved, go", "2026-11-08T13:00:00Z")
    request = request_for(
        repository_with_origin,
        sandbox_vault,
        inbox,
        recording_forge,
        recording_launcher,
        approval,
    )

    report = apply_pull_request(request)

    assert report["merge"] == "merged"
    assert {result["status"] for result in report["results"]} == {"recorded"}
    entry = (
        sandbox_vault
        / "Second Brain"
        / "Inspiration"
        / "Eric Clemmons - PBT MBT and oracles.md"
    )
    entry_text = entry.read_text()
    assert "status: filed" in entry_text and "  - topic/engineering" in entry_text
    assert "## What to steal\n- model the system as a state machine" in entry_text
    moc_text = (
        sandbox_vault / "Second Brain" / "Atlas" / "Engineering MOC.md"
    ).read_text()
    assert moc_text.index("[[Eric Clemmons - PBT MBT and oracles]]") < moc_text.index(
        "## Best of"
    )
    [(host, session, brief)] = recording_launcher.launches
    assert (host, session) == ("chise", "ril-agent-state-machines")
    assert f"> {LUCAS_NOTE}" in brief and "> approved, go" in brief
    for card in group["cards"]:
        assert "#agent-work-done" in (inbox / card["capture"]).read_text()


def test_running_apply_again_changes_nothing(
    repository_with_origin,
    sandbox_vault,
    recording_forge,
    recording_launcher,
    proposed_group,
):
    _, inbox = proposed_group
    approval = recording_forge.comment(1, "approved", "2026-11-08T13:00:00Z")
    request = request_for(
        repository_with_origin,
        sandbox_vault,
        inbox,
        recording_forge,
        recording_launcher,
        approval,
    )
    apply_pull_request(request)
    moc_before = (
        sandbox_vault / "Second Brain" / "Atlas" / "Engineering MOC.md"
    ).read_text()

    second = apply_pull_request(request)

    assert {result["status"] for result in second["results"]} == {"already-done"}
    assert second["merge"] == "already-merged"
    assert len(recording_launcher.launches) == 1
    assert (
        sandbox_vault / "Second Brain" / "Atlas" / "Engineering MOC.md"
    ).read_text() == moc_before


def test_an_approval_older_than_an_added_card_does_not_cover_it(
    repository_with_origin,
    sandbox_vault,
    write_capture,
    recording_forge,
    recording_launcher,
    proposed_group,
):
    group, inbox = proposed_group
    approval = recording_forge.comment(1, "approved", "2026-11-08T13:00:00Z")
    late = copy.deepcopy(group["cards"][1])
    late.update(capture="Tweet from Late (2026-11-08 14-30-00).md", action="drop")
    write_capture(inbox, late["capture"], "[[ReadItLater]] [[Tweet]]\n")
    extension = {**group, "target_pull_request": 1, "cards": [late]}
    propose_groups(
        ProposalContext(repository_with_origin, inbox, recording_forge, EXTENDED_AT),
        [extension],
    )

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

    assert report["not_covered_by_the_approval"] == [late["capture"]]
    assert report["merge"] == "not-merged"
    assert "#agent-work-done" not in (inbox / late["capture"]).read_text()
