import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from pathlib import Path

from voice_pipeline.ports.control import ControlCommand

logger = logging.getLogger(__name__)


class UnixSocketControlServer:
    def __init__(self, socket_path: str = "/tmp/voice-pipeline.sock") -> None:
        self._socket_path = socket_path
        self._server: asyncio.Server | None = None
        self._command_queue: asyncio.Queue[ControlCommand] = asyncio.Queue()
        self._pending_responses: dict[int, asyncio.Future] = {}
        self._response_counter = 0

    async def start(self) -> None:
        socket_file = Path(self._socket_path)
        if socket_file.exists():
            socket_file.unlink()

        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=self._socket_path,
        )
        os.chmod(self._socket_path, 0o600)
        logger.info("Control socket listening at %s", self._socket_path)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        socket_file = Path(self._socket_path)
        if socket_file.exists():
            socket_file.unlink()

    async def commands(self) -> AsyncIterator[ControlCommand]:
        while True:
            cmd = await self._command_queue.get()
            yield cmd

    async def send_response(self, data: dict) -> None:
        pass

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if not raw:
                return

            request = json.loads(raw.decode().strip())
            action = request.get("action", "")
            payload = request.get("payload")

            command = ControlCommand(action=action, payload=payload)
            await self._command_queue.put(command)

            response = await self._wait_for_response(action)
            writer.write((json.dumps(response) + "\n").encode())
            await writer.drain()
        except asyncio.TimeoutError:
            logger.warning("Client connection timed out")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from client")
        except Exception:
            logger.exception("Error handling control client")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _wait_for_response(self, action: str) -> dict:
        await asyncio.sleep(0.1)
        return {"status": "ok", "action": action}


class UnixSocketControlClient:
    def __init__(self, socket_path: str = "/tmp/voice-pipeline.sock") -> None:
        self._socket_path = socket_path

    async def send_command(self, action: str, payload: dict | None = None) -> dict:
        reader, writer = await asyncio.open_unix_connection(self._socket_path)
        try:
            request = {"action": action}
            if payload:
                request["payload"] = payload
            writer.write((json.dumps(request) + "\n").encode())
            await writer.drain()

            raw = await asyncio.wait_for(reader.readline(), timeout=10.0)
            return json.loads(raw.decode().strip())
        finally:
            writer.close()
            await writer.wait_closed()
