import asyncio
import json
import tempfile
from pathlib import Path
from uuid import uuid4

import websockets

from codex_client_context import ClientContext, read_context
from codex_client_transport import forward_connection


async def request(connection, method, parameters, identifier=1):
    await connection.send(
        json.dumps({"id": identifier, "method": method, "params": parameters})
    )
    while True:
        response = json.loads(await connection.recv())
        if "method" not in response and response.get("id") == identifier:
            return response


def test_websocket_adapter_binds_each_client_before_turns_and_rejects_competing_resume():
    async def exercise(directory):
        observed = []
        resolved_directories = []

        async def server(connection):
            async for encoded in connection:
                message = json.loads(encoded)
                method = message.get("method")
                parameters = message.get("params") or {}
                if method == "config/read":
                    resolved_directories.append(parameters["cwd"])
                    result = {
                        "config": {
                            "shell_environment_policy": {"exclude": None, "set": None}
                        }
                    }
                elif method == "thread/start":
                    result = {"thread": {"id": str(uuid4()), "ephemeral": False}}
                elif method == "turn/start":
                    observed.append(
                        read_context(directory / "contexts", parameters["threadId"])
                    )
                    result = {"turn": {"id": "turn"}}
                else:
                    result = {}
                await connection.send(
                    json.dumps({"id": message["id"], "result": result})
                )

        async with websockets.unix_serve(server, str(directory / "upstream.sock")):
            listeners = []
            clients = []
            try:
                for pane in ["first", "second"]:
                    environment = {
                        "HERDR_PANE_ID": pane,
                        "PATH": pane,
                        "PWD": str(directory / pane),
                    }
                    configuration = {"developer_instructions": "instructions-" + pane}

                    async def connect(
                        client, environment=environment, configuration=configuration
                    ):
                        context = ClientContext(
                            directory / "contexts", environment, configuration
                        )
                        await forward_connection(
                            client,
                            directory / "upstream.sock",
                            context,
                            configuration,
                            environment,
                        )

                    endpoint = directory / (pane + ".sock")
                    listeners.append(
                        await websockets.unix_serve(connect, str(endpoint))
                    )
                    clients.append(
                        await websockets.unix_connect(
                            str(endpoint), uri="ws://localhost"
                        )
                    )
                replies = await asyncio.gather(
                    *(request(client, "thread/start", {}) for client in clients)
                )
                identifiers = [reply["result"]["thread"]["id"] for reply in replies]
                assert set(resolved_directories) == {
                    str(directory / "first"),
                    str(directory / "second"),
                }
                await asyncio.gather(
                    *(
                        request(client, "turn/start", {"threadId": identifier})
                        for client, identifier in zip(clients, identifiers)
                    )
                )
                assert {item["environment"]["HERDR_PANE_ID"] for item in observed} == {
                    "first",
                    "second",
                }
                assert {item["developer_instructions"] for item in observed} == {
                    "instructions-first",
                    "instructions-second",
                }
                conflict = await request(
                    clients[1], "thread/resume", {"threadId": identifiers[0]}
                )
                assert "another Codex client" in conflict["error"]["message"]
                unrelated = await request(
                    clients[1], "turn/start", {"threadId": identifiers[0]}
                )
                assert "error" in unrelated
                assert len(observed) == 2
            finally:
                await asyncio.gather(*(client.close() for client in clients))
                for listener in listeners:
                    listener.close()
                await asyncio.gather(
                    *(listener.wait_closed() for listener in listeners)
                )
            assert all(
                read_context(directory / "contexts", identifier) is None
                for identifier in identifiers
            )

    with tempfile.TemporaryDirectory(dir="/tmp") as directory:
        asyncio.run(exercise(Path(directory)))
