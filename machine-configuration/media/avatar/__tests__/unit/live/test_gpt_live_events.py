import asyncio
import base64

import gpt_live
from live_events import AssistantSaid, Audio, Failed, Usage, UserSaid
from test_gpt_live_tasks import ScriptedSocket


def translated(events):
    voice = gpt_live.GptLive()
    voice.socket = ScriptedSocket(events)
    voice.user_since_last_task = ""
    voice.recent_user = ""

    async def collect():
        return [event async for event in voice.events()]

    return asyncio.run(collect())


def test_each_event_kind_becomes_its_domain_event():
    pcm = b"\x01\x02"
    assert translated(
        [
            {
                "type": "session.output_audio.delta",
                "delta": base64.b64encode(pcm).decode(),
            },
            {"type": "session.input_transcript.delta", "delta": "hi"},
            {"type": "session.output_transcript.delta", "delta": "hello"},
            {"type": "session.usage.updated", "usage": {"tokens": 3}},
            {"type": "error", "error": {"code": "x"}},
        ]
    ) == [
        Audio(pcm),
        UserSaid("hi"),
        AssistantSaid("hello"),
        Usage({"tokens": 3}),
        Failed('{"code": "x"}'),
    ]


def test_unknown_events_are_ignored():
    assert translated([{"type": "session.something.else"}]) == []


def test_the_stream_ends_at_session_close_with_its_usage():
    assert translated(
        [
            {"type": "session.closed", "usage": {"tokens": 9}},
            {"type": "session.input_transcript.delta", "delta": "late"},
        ]
    ) == [Usage({"tokens": 9})]


def test_a_close_without_usage_reports_empty_usage():
    assert translated([{"type": "session.closed"}]) == [Usage({})]
