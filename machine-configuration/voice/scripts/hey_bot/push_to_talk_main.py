from __future__ import annotations

from hey_bot.assistant_gateway import AssistantGateway
from hey_bot.desktop_notifier import DesktopNotifier
from hey_bot.gateway_reply_speech import (
    UNPARSABLE_REPLY_SPEECH,
    UNREACHABLE_GATEWAY_SPEECH,
    FailureSpeech,
)
from hey_bot.push_to_talk_capture import PushToTalkCapture
from hey_bot.push_to_talk_session import PushToTalkSession
from hey_bot.runtime_environment import gateway_settings, speech_voice
from hey_bot.speech_synthesizer import SpeechSynthesizer


def build_session() -> PushToTalkSession:
    return PushToTalkSession(
        capture=PushToTalkCapture(),
        notifier=DesktopNotifier(),
        gateway=AssistantGateway(gateway_settings()),
        synthesizer=SpeechSynthesizer(speech_voice()),
        failure_speech=FailureSpeech(
            unreachable=UNREACHABLE_GATEWAY_SPEECH,
            unparsable=UNPARSABLE_REPLY_SPEECH,
        ),
    )


def main() -> None:
    build_session().run()


if __name__ == "__main__":
    main()
