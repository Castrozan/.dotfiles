import asyncio
import json

import websockets

from codex_client_context import ContextConflict
from codex_client_protocol import ClientProtocol, failure
from codex_upstream import Upstream


MAXIMUM_MESSAGE_BYTES = 64 * 1024 * 1024


async def forward_connection(
    client, upstream_socket, context, configuration, environment
):
    protocol = ClientProtocol(context, configuration, environment)
    try:
        async with websockets.unix_connect(
            str(upstream_socket),
            uri="ws://localhost",
            max_size=MAXIMUM_MESSAGE_BYTES,
            max_queue=4,
        ) as upstream:
            dispatcher = Upstream(upstream)

            async def requests():
                async for encoded in client:
                    message = json.loads(encoded)
                    try:
                        resolved = await dispatcher.prepare(
                            message, context, protocol.working_directory
                        )
                        request = protocol.request(message, resolved)
                    except (
                        ContextConflict,
                        ValueError,
                        TypeError,
                        TimeoutError,
                    ) as error:
                        await client.send(
                            json.dumps(failure(message.get("id"), str(error)))
                        )
                        continue
                    await upstream.send(json.dumps(request))

            async def responses():
                async for encoded in upstream:
                    message = json.loads(encoded)
                    if dispatcher.receive(message):
                        continue
                    await client.send(json.dumps(protocol.response(message)))

            tasks = [asyncio.create_task(requests()), asyncio.create_task(responses())]
            try:
                completed, _ = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )
                for task in completed:
                    task.result()
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
    except (OSError, websockets.ConnectionClosed):
        await client.close(code=1011, reason="Shared Codex server disconnected")
    finally:
        protocol.close()
