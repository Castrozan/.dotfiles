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
        self._command_handlers = {
            "join": self._join,
            "leave": self._leave,
            "status": self._status,
            "speak": self._speak,
        }

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
        handler = self._command_handlers.get(request["command"])
        if handler is None:
            return {"error": "unknown_command"}
        try:
            return await handler(request)
        except (VoiceCallError, SpeechSynthesisError) as error:
            return {"error": str(error)}

    async def _join(self, _request):
        return await self._call.join()

    async def _leave(self, _request):
        await self._call.leave()
        return self._call.status()

    async def _status(self, _request):
        return self._call.status()

    async def _speak(self, request):
        return await self._call.speak(request["text"], request["language"])

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
