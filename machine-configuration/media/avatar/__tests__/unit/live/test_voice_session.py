import asyncio
import json

import conversation_addressee
import live_voice
import servant_character
import transcript_log
import voice_session
from conversation_addressee import Addressee
from live_events import TaskRequested, UserSaid
from spoken_turns import Party, SpokenTurn
from voice_session import RoomVoice

FINISHED = object()
LUCAS_NAMES_SASAKI = SpokenTurn(Party.HUMAN, "Lucas: hey Sasaki")


class QueuedVoice:
    name = "queued-live"
    input_rate = 24000
    output_rate = 24000

    def __init__(self, speaking_voice, earlier_conversation):
        self.speaking_voice = speaking_voice
        self.earlier_conversation = earlier_conversation
        self.pending = asyncio.Queue()
        self.connected = False
        self.closed = False
        self.delivered = []
        self.heard = []

    async def connect(self):
        self.connected = True
        return f"session-{self.speaking_voice}"

    async def events(self):
        while (event := await self.pending.get()) is not FINISHED:
            yield event

    async def send_audio(self, pcm):
        self.heard.append(pcm)

    async def deliver(self, task_id, result, final):
        self.delivered.append((task_id, result, final))

    async def close(self):
        self.closed = True

    async def retire(self):
        await self.close()
        self.pending.put_nowait(FINISHED)


def opened_voices():
    opened = []

    def open_voice(speaking_voice, earlier_conversation):
        opened.append(QueuedVoice(speaking_voice, earlier_conversation))
        return opened[-1]

    return opened, open_voice


async def next_event(stream):
    return await asyncio.wait_for(anext(stream), 1)


def test_a_new_voice_replaces_the_old_one_and_the_events_carry_on():
    async def scenario():
        opened, open_voice = opened_voices()
        room = RoomVoice(open_voice, "gleam")
        await room.connect()
        stream = room.events()
        opened[0].pending.put_nowait(UserSaid("oi"))
        assert await next_event(stream) == UserSaid("oi")
        await room.change_to("meridian", [LUCAS_NAMES_SASAKI])
        opened[0].pending.put_nowait(UserSaid("late"))
        opened[1].pending.put_nowait(UserSaid("tudo bem"))
        assert await next_event(stream) == UserSaid("tudo bem")
        await room.send_audio(b"pcm")
        return opened, room

    opened, room = asyncio.run(scenario())
    assert [voice.speaking_voice for voice in opened] == ["gleam", "meridian"]
    assert opened[1].earlier_conversation == [LUCAS_NAMES_SASAKI]
    assert opened[0].closed and opened[1].connected and not opened[1].closed
    assert room.speaking_voice == "meridian"
    assert opened[1].heard == [b"pcm"] and opened[0].heard == []


def test_an_answer_for_a_retired_voice_is_spoken_by_the_new_one_outside_its_tasks():
    async def scenario():
        opened, open_voice = opened_voices()
        room = RoomVoice(open_voice, "gleam")
        stream = room.events()
        opened[0].pending.put_nowait(TaskRequested("old-task", "status"))
        await next_event(stream)
        await room.change_to("meridian", [])
        opened[1].pending.put_nowait(TaskRequested("new-task", "build"))
        await next_event(stream)
        await room.deliver("old-task", "Checking.", False)
        await room.deliver("old-task", "Main is clean.", True)
        await room.deliver("new-task", "Built.", True)
        return opened

    opened = asyncio.run(scenario())
    assert opened[0].delivered == []
    assert opened[1].delivered == [
        (None, "Checking.", False),
        (None, "Main is clean.", True),
        ("new-task", "Built.", True),
    ]


def test_the_voice_follows_whoever_takes_the_room(monkeypatch, tmp_path):
    voices = tmp_path / "voices.json"
    voices.write_text(json.dumps([{"name": "boy", "liveVoice": "meridian"}]))
    assignments = tmp_path / "servant-characters.txt"
    assignments.write_text("Sasaki Kojirou | boy\n")
    monkeypatch.setenv(live_voice.VOICES_ENVIRONMENT_VARIABLE, str(voices))
    monkeypatch.setenv(
        servant_character.CHARACTERS_ENVIRONMENT_VARIABLE, str(assignments)
    )
    monkeypatch.setattr(voice_session, "HOLDER_CHECK_SECONDS", 0.01)
    transcript = tmp_path / "transcript.jsonl"
    transcript_log.append(transcript, "human", "hey Sasaki", speaker="Lucas")
    changes = []

    async def scenario():
        opened, open_voice = opened_voices()
        room = RoomVoice(open_voice, "gleam")
        follow = asyncio.create_task(
            room.follow_the_room_holder(tmp_path, transcript, lambda: changes.append(1))
        )
        await asyncio.sleep(0.05)
        assert len(opened) == 1
        conversation_addressee.hand_to(tmp_path, Addressee("w:p", "Sasaki Kojirou", 1))
        await asyncio.sleep(0.1)
        follow.cancel()
        return opened

    opened = asyncio.run(scenario())
    assert [voice.speaking_voice for voice in opened] == ["gleam", "meridian"]
    assert opened[1].earlier_conversation == [LUCAS_NAMES_SASAKI]
    assert changes == [1]
