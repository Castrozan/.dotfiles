import asyncio
import json
from uuid import uuid4

from codex_client_context import ContextConflict, normalized_identifier
from codex_client_configuration import ThreadPreparation


class Upstream:
    def __init__(self, connection):
        self.connection = connection
        self.pending = {}

    async def request(self, method, parameters):
        identifier = "dotfiles-" + str(uuid4())
        future = asyncio.get_running_loop().create_future()
        self.pending[identifier] = future
        try:
            await self.connection.send(
                json.dumps(
                    {
                        "id": identifier,
                        "method": method,
                        "params": parameters,
                    }
                )
            )
            return await asyncio.wait_for(future, 10)
        finally:
            self.pending.pop(identifier, None)

    def receive(self, message):
        future = self.pending.get(message.get("id"))
        if "method" in message or future is None:
            return False
        if not future.done():
            if "error" in message:
                future.set_exception(ValueError(message["error"]["message"]))
            else:
                future.set_result(message.get("result", {}))
        return True

    async def prepare(self, message, context, working_directory):
        method = message.get("method")
        if method not in {"thread/start", "thread/resume", "thread/fork"}:
            return None
        parameters = message.get("params") or {}
        if parameters.get("ephemeral"):
            return ThreadPreparation(
                {}, working_directory=parameters.get("cwd") or working_directory
            )
        identifier = parameters.get("threadId")
        reserved = False
        try:
            if method == "thread/resume":
                identifier = normalized_identifier(identifier)
                reserved = context.reserve(identifier)
                if context.matches_configuration(identifier):
                    if await self.is_loaded(identifier):
                        return ThreadPreparation({}, reuse_loaded=True)
                else:
                    await self.wait_until_unloaded(identifier)
            directory = await self.thread_working_directory(
                method, parameters, working_directory
            )
            return ThreadPreparation(
                (
                    await self.request(
                        "config/read",
                        {
                            "cwd": directory,
                            "includeLayers": False,
                        },
                    )
                )["config"],
                working_directory=directory,
            )
        except BaseException:
            if reserved:
                context.release(identifier)
            raise

    async def thread_working_directory(self, method, parameters, working_directory):
        if parameters.get("cwd") is not None:
            return parameters["cwd"]
        if method == "thread/start":
            return working_directory
        return (
            await self.request(
                "thread/read",
                {"threadId": parameters.get("threadId"), "includeTurns": False},
            )
        )["thread"]["cwd"]

    async def wait_until_unloaded(self, identifier):
        deadline = asyncio.get_running_loop().time() + 3
        while await self.is_loaded(identifier):
            if asyncio.get_running_loop().time() >= deadline:
                raise ContextConflict(
                    "This thread still runs with another client's environment. "
                    "Finish its turn and close its attachment before resuming here."
                )
            await asyncio.sleep(0.1)

    async def is_loaded(self, identifier):
        cursor = None
        while True:
            page = await self.request(
                "thread/loaded/list", {"cursor": cursor, "limit": 100}
            )
            if identifier in page["data"]:
                return True
            cursor = page.get("nextCursor")
            if not cursor:
                return False
