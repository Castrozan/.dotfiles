import asyncio
import json
import logging

from voice_bridge.speech_synthesis import SpeechSynthesisError
from voice_bridge.voice_call import VoiceCallError

logger = logging.getLogger(__name__)


def encoded_line(message):
    return json.dumps(message, ensure_ascii=False).encode() + b"\n"


class ControlServer:
    def __init__(self, call, feed):
        self._call = call
        self._feed = feed

    async def serve_connection(self, reader, writer):
        try:
            request = json.loads(await reader.readline())
            if request["command"] == "follow":
                await self._stream_transcript(request, writer)
            else:
                writer.write(encoded_line(await self._answer(request)))
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            logger.debug("control client went away")
        finally:
            writer.close()

    async def _answer(self, request):
        try:
            match request["command"]:
                case "join":
                    return await self._call.join()
                case "status":
                    return self._call.status()
                case "speak":
                    return await self._call.speak(request["text"], request["language"])
        except (VoiceCallError, SpeechSynthesisError) as error:
            return {"error": str(error)}
        return {"error": "unknown_command"}

    async def _stream_transcript(self, request, writer):
        after_sequence = request.get("after")
        subscriber = self._feed.subscribe(
            self._feed.last_sequence if after_sequence is None else after_sequence
        )
        try:
            while True:
                writer.write(encoded_line(await subscriber.get()))
                await writer.drain()
        finally:
            self._feed.unsubscribe(subscriber)
