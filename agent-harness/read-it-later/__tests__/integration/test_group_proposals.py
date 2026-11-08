import copy
from datetime import datetime, timezone

import pytest

from evidence.open_groups import captures_listed_in, open_groups
from proposals.cards import CardsInvalid, example_cards_document
from proposals.decision_files import parse_decision_file
from proposals.git_worktrees import file_at_reference, git
from proposals.propose import ProposalContext, propose_groups

FIRST_MOMENT = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
LATER_MOMENT = datetime(2026, 11, 8, 15, 0, tzinfo=timezone.utc)


def example_group() -> dict:
    return copy.deepcopy(example_cards_document()["groups"][0])


def inbox_with_captures(vault, write_capture, group: dict):
    inbox = vault / "ReadItLater Inbox"
    for card in group["cards"]:
        write_capture(
            inbox,
            card["capture"],
            f"[[ReadItLater]] [[Tweet]]\n\n# [x]({card['origin_url']})\n",
        )
    return inbox


def context(repository, inbox, forge, now) -> ProposalContext:
    return ProposalContext(
        repository_directory=repository, inbox_directory=inbox, forge=forge, now=now
    )


def test_a_new_group_opens_one_pull_request_with_its_decision_file(
    repository_with_origin, sandbox_vault, write_capture, recording_forge
):
    group = example_group()
    inbox = inbox_with_captures(sandbox_vault, write_capture, group)

    [result] = propose_groups(
        context(repository_with_origin, inbox, recording_forge, FIRST_MOMENT), [group]
    )

    assert result["branch"].startswith("ril-group-") and result["branch"].endswith(
        "-agent-state-machines"
    )
    decision_text = file_at_reference(
        repository_with_origin,
        f"origin/{result['branch']}",
        f"agent-harness/read-it-later/decisions/{result['branch'].removeprefix('ril-group-')}.md",
    )
    stored = parse_decision_file(decision_text)
    assert [card["added_at"] for card in stored["cards"]] == [
        "2026-11-08T12:00:00+00:00"
    ] * 2
    assert "target_pull_request" not in stored
    assert "| 1 |" in recording_forge.pull_request(1)["body"]
    assert not (repository_with_origin / ".worktrees" / result["branch"]).exists()


def test_a_related_capture_joins_the_open_group_instead_of_a_new_pull_request(
    repository_with_origin, sandbox_vault, write_capture, recording_forge
):
    group = example_group()
    inbox = inbox_with_captures(sandbox_vault, write_capture, group)
    propose_groups(
        context(repository_with_origin, inbox, recording_forge, FIRST_MOMENT), [group]
    )
    related = copy.deepcopy(group["cards"][1])
    related.update(
        capture="Tweet from Related (2026-11-08 14-00-00).md",
        action="drop",
        reason="same idea",
    )
    write_capture(inbox, related["capture"], "[[ReadItLater]] [[Tweet]]\n")
    revised = copy.deepcopy(group["cards"][0])
    revised["reason"] = "Lucas asked for kira"
    extension = {
        **group,
        "target_pull_request": 1,
        "bundle_goal": "extended goal",
        "cards": [revised, related],
    }

    [result] = propose_groups(
        context(repository_with_origin, inbox, recording_forge, LATER_MOMENT),
        [extension],
    )

    assert len(recording_forge.pull_requests) == 1
    assert (result["added"], result["revised"]) == (
        [related["capture"]],
        [revised["capture"]],
    )
    groups = open_groups(
        repository_with_origin, recording_forge.open_pull_requests("ril-group-")
    )
    assert related["capture"] in captures_listed_in(groups)
    assert groups[0]["bundle_goal"] == "extended goal"
    stored = parse_decision_file(
        file_at_reference(
            repository_with_origin,
            f"origin/{result['branch']}",
            groups[0]["decision_file"],
        )
    )
    added_at_by_capture = {
        card["capture"]: card["added_at"] for card in stored["cards"]
    }
    assert added_at_by_capture[revised["capture"]] == "2026-11-08T12:00:00+00:00"
    assert added_at_by_capture[related["capture"]] == "2026-11-08T15:00:00+00:00"
    assert stored["cards"][0]["reason"] == "Lucas asked for kira"
    assert (
        "<!-- ril-watcher -->"
        in recording_forge.pull_request(1)["comments"][-1]["body"]
    )
    assert (
        len(
            git(
                repository_with_origin, "log", "--oneline", f"origin/{result['branch']}"
            ).splitlines()
        )
        == 3
    )


def test_cards_for_missing_or_finished_captures_are_refused(
    repository_with_origin, sandbox_vault, write_capture, recording_forge
):
    group = example_group()
    inbox = sandbox_vault / "ReadItLater Inbox"
    write_capture(inbox, group["cards"][0]["capture"], "body\n#agent-work-done\n")

    with pytest.raises(CardsInvalid) as invalid:
        propose_groups(
            context(repository_with_origin, inbox, recording_forge, FIRST_MOMENT),
            [group],
        )

    assert len(invalid.value.problems) == 2
    assert recording_forge.pull_requests == {}


def test_a_capture_already_in_an_open_group_cannot_open_another(
    repository_with_origin, sandbox_vault, write_capture, recording_forge
):
    group = example_group()
    inbox = inbox_with_captures(sandbox_vault, write_capture, group)
    propose_groups(
        context(repository_with_origin, inbox, recording_forge, FIRST_MOMENT), [group]
    )
    rival = {**example_group(), "topic_slug": "rival-topic"}

    with pytest.raises(CardsInvalid, match="already in open group #1"):
        propose_groups(
            context(repository_with_origin, inbox, recording_forge, LATER_MOMENT),
            [rival],
        )
    assert len(recording_forge.pull_requests) == 1
