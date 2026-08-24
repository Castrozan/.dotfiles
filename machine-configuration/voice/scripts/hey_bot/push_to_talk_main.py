from __future__ import annotations

from assistant_gateway import AssistantGateway
from desktop_notifier import DesktopNotifier
from gateway_reply_speech import (
    UNPARSABLE_REPLY_SPEECH,
    UNREACHABLE_GATEWAY_SPEECH,
    FailureSpeech,
)
from push_to_talk_capture import PushToTalkCapture
from push_to_talk_session import PushToTalkSession
from runtime_environment import gateway_settings, speech_voice
from speech_synthesizer import SpeechSynthesizer


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
