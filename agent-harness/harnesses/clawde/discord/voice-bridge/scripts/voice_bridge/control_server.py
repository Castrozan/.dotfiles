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
            "catalog": self._catalog,
            "character": self._character,
            "model": self._model,
        }

    async def serve_connection(self, reader, writer):
        try:
            request = json.loads(await asyncio.wait_for(reader.readline(), timeout=5))
            if not isinstance(request, dict) or not isinstance(
                request.get("command"), str
            ):
                raise ValueError("invalid_request")
            if request["command"] == "follow":
                await self._stream_transcript(request, writer)
            else:
                writer.write(encoded_line(await self._answer(request)))
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            logger.debug("control client went away")
        except (ValueError, KeyError, TypeError, TimeoutError):
            writer.write(encoded_line({"error": "invalid_request"}))
            await writer.drain()
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
        return await self._call.join(
            preferred=_request.get("preferred"),
            follow=_request.get("follow_listener") is True,
        )

    async def _leave(self, _request):
        await self._call.leave()
        return self._call.status()

    async def _status(self, _request):
        return self._call.status()

    async def _speak(self, request):
        return await self._call.speak(
            request["text"], request["language"], request.get("generation")
        )

    async def _catalog(self, _request):
        return self._call.capabilities()

    async def _character(self, request):
        return await self._call.select_character(request["name"])

    async def _model(self, request):
        return await self._call.select_model(request["name"])

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
