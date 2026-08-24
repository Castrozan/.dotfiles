from hey_bot.assistant_gateway import GatewayReply, GatewayReplyKind


class RecordingConsole:
    def __init__(self):
        self.lines = []
        self.error_lines = []
        self.written_text = []

    def write_line(self, message):
        self.lines.append(message)

    def write_text(self, text):
        self.written_text.append(text)

    def write_error_line(self, message):
        self.error_lines.append(message)


class RecordingNotifier:
    def __init__(self):
        self.bodies = []

    def notify(self, body):
        self.bodies.append(body)


class RecordingSynthesizer:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


class FakeTranscriptionLog:
    def __init__(self, recent_transcription=""):
        self.appended = []
        self._recent_transcription = recent_transcription

    def append(self, text):
        self.appended.append(text)

    def recent_lines(self):
        return self._recent_transcription


class FakeGateway:
    def __init__(self, reply):
        self.reply = reply
        self.prompts = []

    def ask(self, message_content):
        self.prompts.append(message_content)
        return self.reply


def content_reply(content):
    return GatewayReply(GatewayReplyKind.CONTENT, content=content)


def unreachable_reply():
    return GatewayReply(GatewayReplyKind.UNREACHABLE)


def unparsable_reply(raw_response):
    return GatewayReply(GatewayReplyKind.UNPARSABLE, raw_response=raw_response)
