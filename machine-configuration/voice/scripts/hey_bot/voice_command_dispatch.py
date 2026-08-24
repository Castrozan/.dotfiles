from __future__ import annotations

from collections.abc import Callable, Iterable

from hey_bot.assistant_gateway import AssistantGateway, GatewayReplyKind
from hey_bot.console_output import ConsoleOutput
from hey_bot.conversation_actions import (
    AnnounceAction,
    ConversationAction,
    LogTranscriptionAction,
    NotifyAction,
    RaiseFollowupSignalAction,
    SaveWaitContextAction,
    SpeakAction,
)
from hey_bot.gateway_reply_speech import FailureSpeech, spoken_reply
from hey_bot.transcription_log import TranscriptionLog
from hey_bot.transcription_text import collapse_whitespace

IGNORE_REPLY = "IGNORE"
WAIT_REPLY = "WAIT"
NONSENSICAL_INPUT_MESSAGE = "hey-bot: nonsensical input, skipping TTS"
MID_SENTENCE_MESSAGE = "hey-bot: mid-sentence detected, waiting for continuation"
REPLY_PREVIEW_LIMIT = 200
RAW_RESPONSE_PREVIEW_LIMIT = 300

COMMAND_PROMPT_RULES = (
    "[Voice input from microphone transcription. Rules: (1) Respond concisely for TTS"
    " playback, max 3 sentences. (2) Match spoken language (English or Portuguese)."
    " (3) Never include file paths, code blocks, URLs, or technical formatting. (4) If"
    " the transcription is nonsensical, garbled, or clearly not directed at you,"
    " respond with exactly IGNORE and nothing else. (5) If the transcription appears"
    " cut mid-sentence or the user seems to still be speaking, respond with exactly"
    " WAIT and nothing else. (6) If the transcription appears to be your OWN previous"
    " TTS response being re-transcribed by the microphone (sounds like something an AI"
    " assistant would say rather than a human), respond with exactly IGNORE and nothing"
    " else — this prevents feedback loops when using speakers.]"
)


def command_prompt(command_text: str, recent_transcription: str) -> str:
    return (
        f"{COMMAND_PROMPT_RULES}\n\n"
        f"[Recent ambient transcription for context:]\n{recent_transcription}\n\n"
        f"[Command:]\n{command_text}"
    )


def actions_for_command(command_text: str) -> tuple[ConversationAction, ...]:
    return (
        AnnounceAction(f"hey-bot: command: '{command_text}'"),
        LogTranscriptionAction(f"[COMMAND] {command_text}"),
        NotifyAction(command_text),
    )


def actions_for_reply(
    command_text: str, reply_text: str
) -> tuple[ConversationAction, ...]:
    reported: tuple[ConversationAction, ...] = (
        AnnounceAction(f"hey-bot: response: '{reply_text[:REPLY_PREVIEW_LIMIT]}'"),
        LogTranscriptionAction(f"[RESPONSE] {reply_text}"),
    )
    if reply_text == IGNORE_REPLY:
        return reported + (AnnounceAction(NONSENSICAL_INPUT_MESSAGE),)
    if reply_text == WAIT_REPLY:
        return reported + (
            AnnounceAction(MID_SENTENCE_MESSAGE),
            SaveWaitContextAction(command_text),
            RaiseFollowupSignalAction(),
        )
    return reported + (SpeakAction(reply_text), RaiseFollowupSignalAction())


class VoiceCommandDispatcher:
    def __init__(
        self,
        gateway: AssistantGateway,
        transcription_log: TranscriptionLog,
        perform_actions: Callable[[Iterable[ConversationAction]], None],
        console: ConsoleOutput,
        failure_speech: FailureSpeech,
    ):
        self._gateway = gateway
        self._transcription_log = transcription_log
        self._perform_actions = perform_actions
        self._console = console
        self._failure_speech = failure_speech

    def run(self, raw_command_text: str) -> None:
        command_text = collapse_whitespace(raw_command_text)
        self._perform_actions(actions_for_command(command_text))
        reply = self._gateway.ask(
            command_prompt(command_text, self._transcription_log.recent_lines())
        )
        if reply.kind is GatewayReplyKind.UNPARSABLE:
            preview = reply.raw_response[:RAW_RESPONSE_PREVIEW_LIMIT]
            self._console.write_error_line(f"hey-bot: gateway raw response: {preview}")
        self._perform_actions(
            actions_for_reply(command_text, spoken_reply(reply, self._failure_speech))
        )
