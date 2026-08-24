from __future__ import annotations

from assistant_gateway import AssistantGateway
from desktop_notifier import DesktopNotifier
from gateway_reply_speech import FailureSpeech, spoken_reply
from push_to_talk_capture import PushToTalkCapture
from speech_synthesizer import SpeechSynthesizer

NO_SPEECH_NOTIFICATION = "No speech detected"
PUSH_TO_TALK_PROMPT_HEADER = (
    "[Voice input — respond concisely for TTS playback."
    " Match spoken language (English or Portuguese).]"
)


def push_to_talk_prompt(transcription: str) -> str:
    return f"{PUSH_TO_TALK_PROMPT_HEADER}\n\n{transcription}"


class PushToTalkSession:
    def __init__(
        self,
        capture: PushToTalkCapture,
        notifier: DesktopNotifier,
        gateway: AssistantGateway,
        synthesizer: SpeechSynthesizer,
        failure_speech: FailureSpeech,
    ):
        self._capture = capture
        self._notifier = notifier
        self._gateway = gateway
        self._synthesizer = synthesizer
        self._failure_speech = failure_speech

    def run(self) -> None:
        self._capture.stop_recorder()
        transcription = self._capture.read_clipboard()
        if not transcription:
            self._notifier.notify(NO_SPEECH_NOTIFICATION)
            return
        self._notifier.notify(transcription)
        reply = self._gateway.ask(push_to_talk_prompt(transcription))
        self._synthesizer.speak(spoken_reply(reply, self._failure_speech))
