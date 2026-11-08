import asyncio
import json

import gpt_live
from live_events import TaskRequested


class ScriptedSocket:
    def __init__(self, events):
        self.events = [json.dumps(event) for event in events]

    def __aiter__(self):
        return self.stream()

    async def stream(self):
        for event in self.events:
            yield event


def heard(text):
    return {"type": "session.input_transcript.delta", "delta": text}


def delegated(task_id):
    return {"type": "session.delegation.created", "delegation": {"id": task_id}}


def tasks_from(events):
    voice = gpt_live.GptLive()
    voice.socket = ScriptedSocket(events)
    voice.user_since_last_task = ""
    voice.recent_user = ""

    async def collect():
        return [
            event async for event in voice.events() if isinstance(event, TaskRequested)
        ]

    return asyncio.run(collect())


def test_each_task_carries_what_was_said_since_the_previous_one():
    assert tasks_from(
        [
            heard("Check the "),
            heard("disk."),
            delegated("a"),
            heard("And the build?"),
            delegated("b"),
        ]
    ) == [TaskRequested("a", "Check the disk."), TaskRequested("b", "And the build?")]


def test_a_task_with_nothing_new_said_falls_back_to_the_recent_words():
    assert tasks_from([heard("Check the disk."), delegated("a"), delegated("b")]) == [
        TaskRequested("a", "Check the disk."),
        TaskRequested("b", "Check the disk."),
    ]
