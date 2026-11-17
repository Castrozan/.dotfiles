import asyncio
import json
import logging

from voice_bridge.voice_call import VoiceCallError
from voice_provider.clip_wire import read_clip

logger = logging.getLogger(__name__)


def encoded_line(message):
    return json.dumps(message, ensure_ascii=False).encode() + b"\n"


async def read_request(reader):
    request = json.loads(await asyncio.wait_for(reader.readline(), timeout=5))
    if not isinstance(request, dict) or not isinstance(request.get("command"), str):
        raise ValueError("invalid_request")
    return request


class ControlServer:
    def __init__(self, call, capture):
        self._call = call
        self._capture = capture
        self._connections = set()
        self._command_handlers = {
            "join": self._join,
            "leave": self._leave,
            "status": self._status,
            "hush": self._hush,
        }
        self._connection_handlers = {
            "capture": self._stream_capture,
            "play": self._play_clip,
        }

    async def serve_connection(self, reader, writer):
        connection = asyncio.current_task()
        self._connections.add(connection)
        try:
            request = await read_request(reader)
            handler = self._connection_handlers.get(request["command"])
            if handler is not None:
                await handler(request, reader, writer)
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
            self._connections.discard(connection)

    async def close(self):
        connections = tuple(self._connections)
        for connection in connections:
            connection.cancel()
        await asyncio.gather(*connections, return_exceptions=True)

    async def _answer(self, request):
        handler = self._command_handlers.get(request["command"])
        if handler is None:
            return {"error": "unknown_command"}
        try:
            return await handler(request)
        except VoiceCallError as error:
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

    async def _hush(self, _request):
        return self._call.hush()

    async def _play_clip(self, request, reader, writer):
        pcm, sample_rate = await read_clip(request, reader)
        try:
            reply = await self._call.play_clip(pcm, sample_rate)
        except VoiceCallError as error:
            reply = {"error": str(error)}
        writer.write(encoded_line(reply))
        await writer.drain()

    async def _stream_capture(self, _request, _reader, writer):
        subscriber = self._capture.subscribe()
        try:
            while True:
                writer.write(await subscriber.get())
                await writer.drain()
        finally:
            self._capture.unsubscribe(subscriber)
