import asyncio

import agent_route
import conversation_addressee
import live_bridge
import transcript_log
from a2a_fakes import install_a2a, pane_reports
from agent_route import AgentReport
from conversation_addressee import Addressee
from live_events import AssistantSaid, Audio, Failed, TaskRequested, Usage, UserSaid


class FakeVoice:
    name = "fake-live"
    output_rate = 24000

    def __init__(self, events=()):
        self.scripted = list(events)
        self.delivered = []

    async def events(self):
        for event in self.scripted:
            yield event

    async def deliver(self, task_id, result, final):
        self.delivered.append((task_id, result, final))


class SilentSpeaker:
    def __init__(self):
        self.played = []

    def play(self, pcm):
        self.played.append(pcm)

    def buffered_seconds(self):
        return 0

    def clear(self):
        pass


def conversation(tmp_path, voice):
    return live_bridge.LiveConversation(voice, tmp_path, SilentSpeaker(), "microphone")


MAIN_IS_CLEAN = (AgentReport("Main is clean.", 1.0, True),)


def asked_agents(monkeypatch, reports=MAIN_IS_CLEAN):
    asked = []

    async def ask_agent(holder, request, number):
        asked.append((holder.pane, request, number))
        for report in reports:
            yield report

    monkeypatch.setattr(live_bridge, "ask_agent", ask_agent)
    monkeypatch.setattr(live_bridge, "WAKE_HANDOVER_SECONDS", 0)
    return asked


def test_a_task_goes_to_whoever_holds_the_floor_and_its_answer_is_spoken(
    tmp_path, monkeypatch
):
    asked = asked_agents(monkeypatch)
    conversation_addressee.write(tmp_path, Addressee("wW:pQZ", "Voyager", 0))
    voice = FakeVoice()
    asyncio.run(
        conversation(tmp_path, voice).hand_off(TaskRequested("task-1", "is it clean?"))
    )
    assert asked == [("wW:pQZ", "is it clean?", 1)]
    assert voice.delivered == [("task-1", "Main is clean.", True)]


def test_without_a_floor_holder_no_agent_is_asked_and_the_voice_says_so(
    tmp_path, monkeypatch
):
    asked = asked_agents(monkeypatch)
    voice = FakeVoice()
    asyncio.run(conversation(tmp_path, voice).hand_off(TaskRequested("task-2", "x")))
    assert asked == []
    assert voice.delivered == [("task-2", live_bridge.NOBODY_HOLDS_THE_ROOM, True)]


def test_finished_turns_reach_the_transcript_the_wake_reads(tmp_path):
    voice = FakeVoice(
        [UserSaid("Hey Ibaraki, "), UserSaid("check the disk"), AssistantSaid("Sure.")]
    )
    live = conversation(tmp_path, voice)
    asyncio.run(live.handle_events())
    live.write(live.turns.finish())
    entries = transcript_log.read_since(tmp_path / "transcript.jsonl", 0)
    assert [
        (entry["source"], entry["speaker"], entry["text"], entry["turn_finished"])
        for entry in entries
    ] == [
        ("human", None, "Hey Ibaraki, check the disk", True),
        ("avatar", "avatar", "Sure.", True),
    ]
    assert [entry["sequence"] for entry in entries] == [1, 2]


def test_every_event_kind_reaches_its_handler(tmp_path, monkeypatch, capsys):
    asked = asked_agents(monkeypatch)
    conversation_addressee.write(tmp_path, Addressee("wW:pQZ", "Voyager", 0))
    voice = FakeVoice(
        [
            Audio(b"\x00\x00"),
            Usage({"tokens": 3}),
            Failed("boom"),
            TaskRequested("task-3", "is it clean?"),
        ]
    )
    live = conversation(tmp_path, voice)

    async def drive():
        await live.handle_events()
        await asyncio.gather(*live.handoffs)

    asyncio.run(drive())
    assert live.speaker.played == [b"\x00\x00"]
    assert live.usage == {"tokens": 3}
    assert "error: boom" in capsys.readouterr().out
    assert asked == [("wW:pQZ", "is it clean?", 1)]
    assert voice.delivered == [("task-3", "Main is clean.", True)]


def test_each_task_carries_its_own_answer_number_and_every_report_is_relayed(
    tmp_path, monkeypatch
):
    still_working = AgentReport(agent_route.STILL_WORKING, 30.0, False)
    answered = AgentReport("Sim, chegou.", 31.0, True)
    asked = asked_agents(monkeypatch, (still_working, answered))
    conversation_addressee.write(tmp_path, Addressee("wW:pSP", "Anastasia", 0))
    voice = FakeVoice()
    live = conversation(tmp_path, voice)

    async def two_tasks():
        await live.hand_off(TaskRequested("task-4", "first"))
        await live.hand_off(TaskRequested("task-5", "second"))

    asyncio.run(two_tasks())
    assert [number for _, _, number in asked] == [1, 2]
    assert voice.delivered[:2] == [
        ("task-4", agent_route.STILL_WORKING, False),
        ("task-4", "Sim, chegou.", True),
    ]


def test_a_busy_agent_pane_answers_the_live_voice_before_its_turn_ends(
    tmp_path, monkeypatch
):
    install_a2a(tmp_path, monkeypatch)
    monkeypatch.setattr(live_bridge, "WAKE_HANDOVER_SECONDS", 0)
    pane_reports(tmp_path, "working", "⏺ Agent(build)\n⏺ LIVE-ANSWER-1: Sim, chegou.")
    conversation_addressee.write(tmp_path, Addressee("wW:pSP", "Anastasia", 0))
    voice = FakeVoice()
    asyncio.run(conversation(tmp_path, voice).hand_off(TaskRequested("task-6", "oi")))
    assert voice.delivered == [("task-6", "Sim, chegou.", True)]


def test_an_agent_that_never_answers_is_reported_to_the_owner_by_voice(
    tmp_path, monkeypatch
):
    install_a2a(tmp_path, monkeypatch)
    monkeypatch.setattr(live_bridge, "WAKE_HANDOVER_SECONDS", 0)
    pane_reports(tmp_path, "working", "⏺ Agent(build)")
    conversation_addressee.write(tmp_path, Addressee("wW:pSP", "Anastasia", 0))
    voice = FakeVoice()
    asyncio.run(conversation(tmp_path, voice).hand_off(TaskRequested("task-8", "oi")))
    assert voice.delivered[-1] == ("task-8", agent_route.NO_ANSWER_IN_TIME, True)
    assert ("task-8", agent_route.STILL_WORKING, False) in voice.delivered
