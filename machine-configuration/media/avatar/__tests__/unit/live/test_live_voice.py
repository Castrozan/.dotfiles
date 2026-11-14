import asyncio
import json

import conversation_addressee
import gpt_live
import live_voice
import pytest
import servant_character
from conversation_addressee import Addressee
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

CHARACTERS = [
    {"name": "vivi", "cloudVoice": "a", "localVoice": "b", "liveVoice": "coral"},
    {
        "name": "hair-sample-male",
        "cloudVoice": "c",
        "localVoice": "d",
        "liveVoice": "cedar",
    },
    {"name": "no-live-voice", "cloudVoice": "e", "localVoice": "f"},
]
ASSIGNMENTS = (
    "Scheherazade | vivi\nSasaki Kojirou | hair-sample-male\nCirce | no-live-voice\n"
)


@pytest.fixture
def cast(monkeypatch, tmp_path):
    voices = tmp_path / "voices.json"
    voices.write_text(json.dumps(CHARACTERS))
    assignments = tmp_path / "servant-characters.txt"
    assignments.write_text(ASSIGNMENTS)
    monkeypatch.setenv(live_voice.VOICES_ENVIRONMENT_VARIABLE, str(voices))
    monkeypatch.setenv(
        servant_character.CHARACTERS_ENVIRONMENT_VARIABLE, str(assignments)
    )
    return tmp_path


@pytest.mark.parametrize(
    ("servant", "voice"),
    [
        ("Scheherazade", "coral"),
        ("Sasaki Kojirou", "cedar"),
        ("Circe", live_voice.DEFAULT_VOICE),
        ("Unassigned", live_voice.DEFAULT_VOICE),
        (None, live_voice.DEFAULT_VOICE),
    ],
)
def test_a_servant_is_heard_in_the_live_voice_of_its_character(cast, servant, voice):
    assert live_voice.voice_for(servant) == voice


def test_without_the_voice_table_every_servant_keeps_the_default_voice(
    monkeypatch, cast
):
    monkeypatch.delenv(live_voice.VOICES_ENVIRONMENT_VARIABLE)
    assert live_voice.voice_for("Scheherazade") == live_voice.DEFAULT_VOICE


@pytest.mark.parametrize("content", ["not json", "{}"])
def test_an_unreadable_voice_table_keeps_the_default_voice(monkeypatch, cast, content):
    (cast / "voices.json").write_text(content)
    assert live_voice.voice_for("Scheherazade") == live_voice.DEFAULT_VOICE


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    table=st.dictionaries(
        st.sampled_from(["vivi", "hair-sample-male", "vita"]),
        st.text(alphabet="abcdef", min_size=1, max_size=6),
    )
)
def test_the_live_voice_is_whatever_the_table_says_for_the_assigned_character(
    cast, table
):
    (cast / "voices.json").write_text(
        json.dumps(
            [{"name": name, "liveVoice": voice} for name, voice in table.items()]
        )
    )
    assert live_voice.voice_for("Scheherazade") == table.get(
        "vivi", live_voice.DEFAULT_VOICE
    )
    assert live_voice.voice_for("Sasaki Kojirou") == table.get(
        "hair-sample-male", live_voice.DEFAULT_VOICE
    )


def test_the_room_holder_voice_is_read_when_the_holder_already_exists(cast):
    conversation_addressee.hand_to(cast, Addressee("w:p1", "Sasaki Kojirou", 0))
    assert asyncio.run(live_voice.voice_of_the_room_holder(cast)) == "cedar"


def test_the_live_voice_waits_for_the_floor_to_be_given(cast):
    async def hand_over_shortly():
        await asyncio.sleep(0.3)
        conversation_addressee.hand_to(cast, Addressee("w:p1", "Scheherazade", 0))

    async def both():
        handed = asyncio.create_task(hand_over_shortly())
        voice = await live_voice.voice_of_the_room_holder(cast)
        await handed
        return voice

    assert asyncio.run(both()) == "coral"


def test_without_any_holder_the_default_voice_is_used_after_the_wait(monkeypatch, cast):
    monkeypatch.setattr(live_voice, "HOLDER_WAIT_SECONDS", 0.2)
    voice = asyncio.run(live_voice.voice_of_the_room_holder(cast))
    assert voice == live_voice.DEFAULT_VOICE


class RecordingSocket:
    def __init__(self):
        self.sent = []

    async def send(self, message):
        self.sent.append(json.loads(message))

    async def recv(self):
        return json.dumps({"type": "session.started", "session": {"id": "s-1"}})


def started_session_voice(monkeypatch, tmp_path, live):
    socket = RecordingSocket()

    async def connect(*arguments, **options):
        return socket

    key = tmp_path / "key"
    key.write_text("secret")
    monkeypatch.setattr(gpt_live, "KEY_FILE", key)
    monkeypatch.setattr(gpt_live.websockets, "connect", connect)
    asyncio.run(live.connect())
    return socket.sent[0]["session"]["audio"]["output"]["voice"]


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(voice=st.text(min_size=1, max_size=12))
def test_the_live_session_starts_with_the_chosen_voice(monkeypatch, tmp_path, voice):
    assert (
        started_session_voice(monkeypatch, tmp_path, gpt_live.GptLive(voice)) == voice
    )


def test_the_live_session_starts_with_the_default_voice_when_none_is_chosen(
    monkeypatch, tmp_path
):
    assert (
        started_session_voice(monkeypatch, tmp_path, gpt_live.GptLive())
        == live_voice.DEFAULT_VOICE
    )
