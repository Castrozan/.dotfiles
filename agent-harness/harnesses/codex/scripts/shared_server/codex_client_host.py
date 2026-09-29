import asyncio
import json
import os
from pathlib import Path

from codex_client_control import control_directory, proxy_generation
from codex_client_endpoint import ClientEndpoint


class ClientHost:
    def __init__(self):
        self.directory = control_directory(Path(os.environ["CODEX_HOME"]))
        self.endpoints = set()
        self.stopped = asyncio.Event()

    async def expire(self, endpoint):
        await endpoint.close()
        self.endpoints.discard(endpoint)

    async def respond(self, message):
        if message["method"] == "status":
            return {
                "generation": proxy_generation(os.environ["CODEX_LAUNCHER_BINARY"]),
                "pid": os.getpid(),
            }
        if message["method"] == "shutdown":
            if any(
                endpoint.client is not None or endpoint.owner_is_alive()
                for endpoint in self.endpoints
            ):
                raise RuntimeError(
                    "Close attached Codex clients before activating the upgraded proxy, or use --no-daemon."
                )
            self.stopped.set()
            return {}
        if message["method"] != "register":
            raise ValueError("Unknown Codex client control request")
        if len(self.endpoints) >= 128:
            raise RuntimeError(
                "Codex proxy has reached its 128-client connection limit"
            )
        environment = message["environment"]
        environment["CODEX_LAUNCHER_BINARY"] = os.environ["CODEX_LAUNCHER_BINARY"]
        environment["CODEX_HOME"] = os.environ["CODEX_HOME"]
        process_identifier = message["processId"]
        if not isinstance(process_identifier, int) or process_identifier <= 0:
            raise ValueError("Codex client processId must be a positive integer")
        endpoint = ClientEndpoint(
            self.directory,
            environment,
            message["configuration"],
            process_identifier,
            self.expire,
        )
        self.endpoints.add(endpoint)
        try:
            await endpoint.start()
        except BaseException:
            self.endpoints.discard(endpoint)
            raise
        return {"endpoint": str(endpoint.socket)}

    async def connection(self, reader, writer):
        try:
            message = json.loads(await asyncio.wait_for(reader.readline(), 5))
            result = await self.respond(message)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            result = {"error": str(error)}
        try:
            writer.write(json.dumps(result).encode() + b"\n")
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def run(self):
        socket = self.directory / "control.sock"
        socket.unlink(missing_ok=True)
        try:
            async with await asyncio.start_unix_server(
                self.connection, path=str(socket), limit=2 * 1024 * 1024
            ):
                socket.chmod(0o600)
                await self.stopped.wait()
        finally:
            await asyncio.gather(*(endpoint.close() for endpoint in self.endpoints))
            socket.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(ClientHost().run())
