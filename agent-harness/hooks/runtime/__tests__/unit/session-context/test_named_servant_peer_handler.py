import json
import subprocess
import unicodedata
from unittest.mock import Mock

import pytest

from hook_module_loader import import_hyphenated_hook_module

named_servant_peer_handler = import_hyphenated_hook_module("named_servant_peer_handler")

CATALOG_NAMES = [
    servant["name"] for servant in named_servant_peer_handler.SERVANT_CATALOG
]
OWN_SERVANT = "Altera"


def peer(name, servant, harness="claude", pane="w1:p1"):
    return {"name": name, "servant": servant, "harness": harness, "paneId": pane}


@pytest.fixture(autouse=True)
def session_holds_a_servant(monkeypatch):
    monkeypatch.setattr(
        named_servant_peer_handler,
        "servant_for_hook_input",
        lambda hook_input: {"name": OWN_SERVANT},
    )


@pytest.fixture
def peer_directory(monkeypatch):
    def install(*peers):
        directory = Mock(return_value={item["name"]: item for item in peers})
        monkeypatch.setattr(
            named_servant_peer_handler, "live_peer_directory", directory
        )
        return directory

    return install


def context_for(prompt):
    result = named_servant_peer_handler.handle({"prompt": prompt, "session_id": "s"})
    return result.additional_context if result else ""


def without_marks(text):
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(character)
    )


@pytest.mark.parametrize("name", sorted(set(CATALOG_NAMES) - {OWN_SERVANT}))
def test_any_spelling_of_a_live_servant_names_its_a2a_command(name, peer_directory):
    peer_directory(peer("work-pane", name))
    for spelling in (name, name.casefold(), without_marks(name)):
        context = context_for(f"give to {spelling}, please launch a session")
        assert f'a2a ask "{name}" "<task>"' in context
        assert "work-pane" in context


def test_a_servant_name_inside_a_longer_word_is_not_a_mention(peer_directory):
    peer_directory(peer("work-pane", "Rama"))
    assert context_for("the panorama view drama") == ""


def test_a_prompt_without_a_servant_never_reads_the_peer_directory(peer_directory):
    directory = peer_directory(peer("work-pane", "Medea"))
    assert context_for("rebuild the machine") == ""
    directory.assert_not_called()


def test_the_session_is_never_routed_to_itself(peer_directory):
    peer_directory(peer("me", OWN_SERVANT), peer("other", "Medea"))
    assert context_for(f"{OWN_SERVANT} tell me a story") == ""


def test_a_catalog_name_with_no_live_holder_adds_nothing(peer_directory):
    peer_directory(peer("work-pane", "Medea"))
    assert context_for("ask Voyager about the probe") == ""


def test_two_holders_of_one_servant_are_addressed_by_peer_name(peer_directory):
    peer_directory(peer("first", "Medea"), peer("second", "Medea"))
    context = context_for("give it to Medea")
    assert 'a2a ask "first" "<task>"' in context
    assert 'a2a ask "second" "<task>"' in context


def test_a_session_without_a_servant_gets_nothing(monkeypatch, peer_directory):
    peer_directory(peer("work-pane", "Medea"))
    monkeypatch.setattr(
        named_servant_peer_handler, "servant_for_hook_input", lambda hook_input: None
    )
    assert context_for("give it to Medea") == ""


@pytest.mark.parametrize(
    "outcome",
    [
        FileNotFoundError("a2a"),
        subprocess.TimeoutExpired("a2a", 1.0),
        Mock(returncode=1, stdout=""),
        Mock(returncode=0, stdout="not json"),
        Mock(returncode=0, stdout=json.dumps(["unexpected"])),
    ],
    ids=["missing", "slow", "failing", "garbled", "wrong-shape"],
)
def test_an_unavailable_directory_stays_silent(monkeypatch, outcome):
    monkeypatch.setattr(
        named_servant_peer_handler.subprocess, "run", Mock(side_effect=[outcome])
    )
    assert context_for("give it to Medea") == ""
