import copy
import json
from datetime import datetime, timezone

from commands import command_probe
from gather import GatherSources, gather_document
from origins.transport import OriginTransport
from proposals.cards import example_cards_document
from proposals.propose import ProposalContext, propose_groups
from ril import build_parser

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
FRESH = "Tweet from Fresh (2026-11-08 11-00-00).md"


def offline_transport() -> OriginTransport:
    post = {"tweet": {"text": "fresh idea", "author": {"screen_name": "someone"}}}

    def run(arguments: list[str]) -> str:
        return json.dumps(post) + "\nhttps://api.fxtwitter.com\napplication/json"

    return OriginTransport(command_runner=run)


def seed_inbox_and_group(repository, vault, write_capture, forge):
    inbox = vault / "ReadItLater Inbox"
    group = copy.deepcopy(example_cards_document()["groups"][0])
    for card in group["cards"]:
        write_capture(
            inbox,
            card["capture"],
            f"[[ReadItLater]] [[Tweet]]\n\n# [x]({card['origin_url']})\n",
        )
    propose_groups(ProposalContext(repository, inbox, forge, NOW), [group])
    write_capture(
        inbox,
        FRESH,
        "[[ReadItLater]] [[Tweet]]\n\n# [s](https://x.com/someone/status/42)\n\nfile under agents\n",
    )
    return inbox


def test_gather_reads_only_captures_no_open_group_lists_with_their_evidence(
    repository_with_origin, sandbox_vault, write_capture, recording_forge
):
    inbox = seed_inbox_and_group(
        repository_with_origin, sandbox_vault, write_capture, recording_forge
    )
    recording_forge.closed.append(
        {
            "number": 180,
            "headRefName": "ril-tweet-from-someone",
            "title": "old",
            "body": "status/42",
            "state": "CLOSED",
        }
    )
    sources = GatherSources(
        inbox,
        sandbox_vault,
        repository_with_origin,
        recording_forge,
        offline_transport(),
    )

    document = gather_document(sources, NOW)

    [capture] = document["captures"]
    assert capture["name"] == FRESH
    assert capture["lucas_note"] == "file under agents"
    assert capture["origin"]["text"] == "fresh idea"
    assert capture["evidence"]["second_brain_entries"] == ["Existing entry"]
    assert [
        pull_request["number"]
        for pull_request in capture["evidence"]["closed_pull_requests"]
    ] == [180]
    assert document["open_groups"][0]["captures"] == [
        card["capture"] for card in example_cards_document()["groups"][0]["cards"]
    ]
    assert "Engineering MOC" in document["second_brain"]["mocs"]


def test_probe_wakes_for_an_unlisted_capture_and_an_unanswered_comment(
    repository_with_origin,
    sandbox_vault,
    write_capture,
    recording_forge,
    monkeypatch,
    capsys,
):
    inbox = seed_inbox_and_group(
        repository_with_origin, sandbox_vault, write_capture, recording_forge
    )
    recording_forge.comment(1, "why kira?")
    monkeypatch.setattr("commands.ForgeAdapter", lambda _: recording_forge)
    arguments = build_parser().parse_args(
        ["probe", "--inbox", str(inbox), "--repository", str(repository_with_origin)]
    )

    assert command_probe(arguments) == 0

    assert capsys.readouterr().out.splitlines() == [
        "response 1:comment-1",
        f"capture {FRESH}",
    ]


def test_gather_skips_a_capture_another_run_holds_instead_of_failing(
    repository_with_origin, sandbox_vault, write_capture, recording_forge
):
    inbox = seed_inbox_and_group(
        repository_with_origin, sandbox_vault, write_capture, recording_forge
    )
    claimed_at = NOW.astimezone().replace(tzinfo=None).isoformat(timespec="seconds")
    write_capture(
        inbox,
        "Held.md",
        f"[[ReadItLater]] [[Tweet]]\n\nstatus:: working\nclaimed_by:: kira\nclaimed_at:: {claimed_at}\n",
    )
    sources = GatherSources(
        inbox,
        sandbox_vault,
        repository_with_origin,
        recording_forge,
        offline_transport(),
    )

    document = gather_document(sources, NOW)

    assert [capture["name"] for capture in document["captures"]] == [FRESH]
