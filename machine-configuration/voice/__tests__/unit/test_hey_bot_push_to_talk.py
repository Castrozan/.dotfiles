from dataclasses import dataclass

from hey_bot.gateway_reply_speech import (
    UNPARSABLE_REPLY_SPEECH,
    UNREACHABLE_GATEWAY_SPEECH,
    FailureSpeech,
)
from hey_bot_boundary_fakes import (
    FakeGateway,
    RecordingNotifier,
    RecordingSynthesizer,
    content_reply,
    unparsable_reply,
    unreachable_reply,
)
from hey_bot.process_execution import CommandResult
from hey_bot.push_to_talk_capture import PushToTalkCapture
from hey_bot.push_to_talk_session import (
    NO_SPEECH_NOTIFICATION,
    PUSH_TO_TALK_PROMPT_HEADER,
    PushToTalkSession,
)

TRANSCRIPTION = "what is the weather"
FAILURE_SPEECH = FailureSpeech(
    unreachable=UNREACHABLE_GATEWAY_SPEECH, unparsable=UNPARSABLE_REPLY_SPEECH
)


@dataclass
class PushToTalkRun:
    commands: list
    notifier: RecordingNotifier
    synthesizer: RecordingSynthesizer
    gateway: FakeGateway


def run_session(clipboard=TRANSCRIPTION, reply=None, recorder_exit_code=0):
    commands = []

    def run_process(arguments, merge_error_output=False):
        commands.append(list(arguments))
        if arguments[0] == "whisp-away":
            return CommandResult(recorder_exit_code, "")
        return CommandResult(0, clipboard)

    session_run = PushToTalkRun(
        commands=commands,
        notifier=RecordingNotifier(),
        synthesizer=RecordingSynthesizer(),
        gateway=FakeGateway(reply or content_reply("The weather is fine.")),
    )
    PushToTalkSession(
        capture=PushToTalkCapture(run_process=run_process),
        notifier=session_run.notifier,
        gateway=session_run.gateway,
        synthesizer=session_run.synthesizer,
        failure_speech=FAILURE_SPEECH,
    ).run()
    return session_run


def test_the_recorder_is_stopped_into_the_clipboard_before_it_is_read():
    session_run = run_session()

    assert session_run.commands == [
        ["whisp-away", "stop", "--clipboard", "true"],
        ["wl-paste"],
    ]


def test_a_failing_recorder_stop_still_reaches_the_notification_and_the_gateway():
    session_run = run_session(recorder_exit_code=1)

    assert session_run.notifier.bodies == [TRANSCRIPTION]
    assert session_run.gateway.prompts
    assert session_run.synthesizer.spoken == ["The weather is fine."]


def test_an_empty_clipboard_reports_no_speech_and_stops_before_the_gateway():
    session_run = run_session(clipboard="")

    assert session_run.notifier.bodies == [NO_SPEECH_NOTIFICATION]
    assert session_run.gateway.prompts == []
    assert session_run.synthesizer.spoken == []


def test_the_prompt_carries_its_own_header_and_the_transcription():
    session_run = run_session()

    assert session_run.gateway.prompts == [
        f"{PUSH_TO_TALK_PROMPT_HEADER}\n\n{TRANSCRIPTION}"
    ]


def test_an_unreachable_gateway_speaks_the_reach_failure():
    session_run = run_session(reply=unreachable_reply())

    assert session_run.synthesizer.spoken == [UNREACHABLE_GATEWAY_SPEECH]


def test_an_unparsable_reply_speaks_the_processing_failure():
    session_run = run_session(reply=unparsable_reply('{"error":"upstream exploded"}'))

    assert session_run.synthesizer.spoken == [UNPARSABLE_REPLY_SPEECH]
