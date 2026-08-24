from hey_bot.conversation_actions import (
    AnnounceAction,
    LogTranscriptionAction,
    NotifyAction,
    RaiseFollowupSignalAction,
    SaveWaitContextAction,
    SpeakAction,
)
from hey_bot.gateway_reply_speech import (
    UNPARSABLE_REPLY_SPEECH,
    UNREACHABLE_GATEWAY_SPEECH,
    FailureSpeech,
)
from hey_bot_boundary_fakes import (
    FakeGateway,
    FakeTranscriptionLog,
    RecordingConsole,
    content_reply,
    unparsable_reply,
    unreachable_reply,
)
from hey_bot.voice_command_dispatch import (
    COMMAND_PROMPT_RULES,
    MID_SENTENCE_MESSAGE,
    NONSENSICAL_INPUT_MESSAGE,
    VoiceCommandDispatcher,
)

COMMAND_TEXT = "hey clever what is the weather"
FAILURE_SPEECH = FailureSpeech(
    unreachable=UNREACHABLE_GATEWAY_SPEECH, unparsable=UNPARSABLE_REPLY_SPEECH
)


def dispatch(reply, command_text=COMMAND_TEXT, recent_transcription=""):
    performed = []
    gateway = FakeGateway(reply)
    console = RecordingConsole()
    dispatcher = VoiceCommandDispatcher(
        gateway=gateway,
        transcription_log=FakeTranscriptionLog(recent_transcription),
        perform_actions=performed.extend,
        console=console,
        failure_speech=FAILURE_SPEECH,
    )
    dispatcher.run(command_text)
    return performed, gateway, console


def test_the_command_is_announced_logged_and_notified_before_the_gateway_answers():
    performed, _gateway, _console = dispatch(content_reply("The weather is fine."))

    assert performed[:3] == [
        AnnounceAction(f"hey-bot: command: '{COMMAND_TEXT}'"),
        LogTranscriptionAction(f"[COMMAND] {COMMAND_TEXT}"),
        NotifyAction(COMMAND_TEXT),
    ]


def test_the_prompt_carries_the_rules_the_recent_context_and_the_command():
    _performed, gateway, _console = dispatch(
        content_reply("Fine."), recent_transcription="[COMMAND] earlier phrase"
    )

    assert gateway.prompts == [
        f"{COMMAND_PROMPT_RULES}\n\n"
        "[Recent ambient transcription for context:]\n[COMMAND] earlier phrase\n\n"
        f"[Command:]\n{COMMAND_TEXT}"
    ]


def test_a_ragged_command_reaches_the_gateway_collapsed():
    _performed, gateway, _console = dispatch(
        content_reply("Fine."), command_text="  hey clever   what   is it  "
    )

    assert gateway.prompts[0].endswith("[Command:]\nhey clever what is it")


def test_a_spoken_reply_is_played_and_reopens_the_followup_window():
    performed, _gateway, _console = dispatch(content_reply("The weather is fine."))

    assert performed[3:] == [
        AnnounceAction("hey-bot: response: 'The weather is fine.'"),
        LogTranscriptionAction("[RESPONSE] The weather is fine."),
        SpeakAction("The weather is fine."),
        RaiseFollowupSignalAction(),
    ]


def test_an_ignore_reply_skips_text_to_speech_and_the_followup_window():
    performed, _gateway, _console = dispatch(content_reply("IGNORE"))

    assert AnnounceAction(NONSENSICAL_INPUT_MESSAGE) in performed
    assert not [action for action in performed if isinstance(action, SpeakAction)]
    assert RaiseFollowupSignalAction() not in performed


def test_a_wait_reply_saves_the_command_as_context_and_stays_silent():
    performed, _gateway, _console = dispatch(content_reply("WAIT"))

    assert performed[3:] == [
        AnnounceAction("hey-bot: response: 'WAIT'"),
        LogTranscriptionAction("[RESPONSE] WAIT"),
        AnnounceAction(MID_SENTENCE_MESSAGE),
        SaveWaitContextAction(COMMAND_TEXT),
        RaiseFollowupSignalAction(),
    ]


def test_an_unreachable_gateway_speaks_the_reach_failure():
    performed, _gateway, _console = dispatch(unreachable_reply())

    assert SpeakAction(UNREACHABLE_GATEWAY_SPEECH) in performed
    assert LogTranscriptionAction(f"[RESPONSE] {UNREACHABLE_GATEWAY_SPEECH}") in (
        performed
    )


def test_an_unparsable_reply_speaks_the_processing_failure_and_reports_the_body():
    performed, _gateway, console = dispatch(
        unparsable_reply('{"error":"upstream exploded"}')
    )

    assert SpeakAction(UNPARSABLE_REPLY_SPEECH) in performed
    assert console.error_lines == [
        'hey-bot: gateway raw response: {"error":"upstream exploded"}'
    ]


def test_a_long_reply_is_announced_in_preview_but_logged_whole():
    long_reply = "sentence " * 40
    performed, _gateway, _console = dispatch(content_reply(long_reply))

    assert performed[3] == AnnounceAction(f"hey-bot: response: '{long_reply[:200]}'")
    assert performed[4] == LogTranscriptionAction(f"[RESPONSE] {long_reply}")
