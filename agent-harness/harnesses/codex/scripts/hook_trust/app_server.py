import asyncio
import json


class CodexStdioConnection:
    def __init__(self, process: asyncio.subprocess.Process):
        self.process = process

    async def send(self, message: str) -> None:
        self.process.stdin.write(message.encode() + b"\n")
        await self.process.stdin.drain()

    async def recv(self) -> bytes:
        line = await self.process.stdout.readline()
        if not line:
            raise RuntimeError("Codex app-server closed the configuration connection")
        return line


class CodexConfigurationClient:
    def __init__(self, connection):
        self.connection = connection
        self.request_number = 0

    async def send(self, message: dict) -> None:
        await self.connection.send(json.dumps(message))

    async def request(self, method: str, parameters: dict) -> dict:
        self.request_number += 1
        await self.send(
            {"id": self.request_number, "method": method, "params": parameters}
        )
        while True:
            response = json.loads(await self.connection.recv())
            if response.get("id") != self.request_number:
                continue
            if "error" in response:
                raise RuntimeError(f"{method}: {response['error']['message']}")
            return response["result"]

    async def initialize(self) -> None:
        await self.request(
            "initialize",
            {
                "clientInfo": {"name": "codex_launcher_hook_trust", "version": "1"},
                "capabilities": {"experimentalApi": True},
            },
        )
        await self.send({"method": "initialized", "params": {}})
