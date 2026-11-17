import shlex
from types import SimpleNamespace
from unittest.mock import Mock

import remote_agent
import remote_talk
import room_reach
from hypothesis import given
from hypothesis import strategies as st

TEXT = st.text(st.characters(blacklist_characters="\x00", blacklist_categories=["Cs"]))
AWKWARD_TEXT = st.text(alphabet="'\"$`\\ \n\t*;&|<>(){}#~!?é漢")
WORDS = st.lists(st.one_of(TEXT, AWKWARD_TEXT), max_size=6)
PANES = st.one_of(TEXT, AWKWARD_TEXT, st.just("w0:p7")).filter(bool)


def remote_words(command):
    assert command[: len(remote_agent.REACH_HOST)] == remote_agent.REACH_HOST
    return shlex.split(command[-1])


@given(words=WORDS)
def test_the_remote_shell_splits_the_command_back_into_the_words_given(words):
    command = remote_agent.on_host("kira", ["avatar-talk", *words])
    assert command[-2] == "kira"
    assert remote_words(command) == ["avatar-talk", *words]


@given(words=WORDS)
def test_the_mac_talk_forwarder_keeps_every_argument_whole(words):
    command = remote_talk.forward_command(words)
    assert remote_words(command) == ["avatar-talk", *words]


@given(words=WORDS, pane=PANES)
def test_the_room_forwarder_keeps_the_pane_and_every_argument_whole(words, pane):
    run = Mock(return_value=SimpleNamespace(returncode=0))
    environment = {
        room_reach.ROOM_VARIABLE: "kira",
        remote_agent.PANE_ENVIRONMENT_VARIABLE: pane,
    }
    room_reach.forwarded_to_the_room(words, environment, "chise", run)
    assert remote_words(run.call_args.args[0]) == [
        "env",
        f"{remote_agent.PANE_ENVIRONMENT_VARIABLE}={pane}",
        "avatar-talk",
        *words,
    ]
