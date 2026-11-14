import asyncio
import json
import logging
import os
import signal
from pathlib import Path

from voice_bridge.agent_conversations import (
    A2AConversation,
    ConversationTurnError,
    HermesConversation,
    live_peer,
)
from voice_bridge.conversation_router import ConversationRouter

CONTROL_CONNECT_RETRY_SECONDS = 1
PENDING_LINE_LIMIT = 64
SPEECH_LANGUAGE = "pt-br"
STAY_SILENT_REPLY = "SILENCIO"
FAILED_TURN_APOLOGY = "Tive um problema para responder agora."
SPOKEN_CALL_INSTRUCTION = (
    "Você está em uma ligação de voz no Discord com o Lucas. Sua resposta será "
    "falada em voz alta: responda em uma ou duas frases curtas, no idioma dele, "
    "sem markdown, listas ou links. A fala abaixo vem de uma transcrição que "
    f"pode ter erros. Se for ruído ou conversa com outra pessoa, responda apenas {STAY_SILENT_REPLY}."
)

logger = logging.getLogger(__name__)


def spoken_turn_prompt(spoken_lines):
    return f"{SPOKEN_CALL_INSTRUCTION}\n\nLucas: {' '.join(spoken_lines)}"


def reply_worth_speaking(reply):
    return bool(reply) and reply.strip(" .\n") != STAY_SILENT_REPLY


class BridgeControl:
    def __init__(self, socket_path):
        self._socket_path = socket_path

    async def _connected(self):
        while True:
            try:
                return await asyncio.open_unix_connection(self._socket_path)
            except (FileNotFoundError, ConnectionRefusedError):
                await asyncio.sleep(CONTROL_CONNECT_RETRY_SECONDS)

    async def spoken_lines(self):
        reader, writer = await self._connected()
        writer.write(json.dumps({"command": "follow"}).encode() + b"\n")
        await writer.drain()
        try:
            while line := await reader.readline():
                text = json.loads(line).get("text")
                if text:
                    yield text
        finally:
            writer.close()
            await writer.wait_closed()

    async def speak(self, text):
        reader, writer = await self._connected()
        request = {"command": "speak", "text": text, "language": SPEECH_LANGUAGE}
        try:
            writer.write(json.dumps(request).encode() + b"\n")
            await writer.drain()
            reply = await reader.readline()
        finally:
            writer.close()
            await writer.wait_closed()
        if reply and "error" in json.loads(reply):
            logger.warning("speech rejected: %s", json.loads(reply)["error"])


def drained_spoken_lines(first_line, pending_lines):
    spoken_lines = [first_line]
    while not pending_lines.empty():
        spoken_lines.append(pending_lines.get_nowait())
    return spoken_lines


async def collect_spoken_lines(transcript_lines, pending_lines):
    async for text in transcript_lines:
        await pending_lines.put(text)


async def answer_spoken_lines(pending_lines, reply_to, speak):
    while True:
        spoken_lines = drained_spoken_lines(await pending_lines.get(), pending_lines)
        try:
            reply = await reply_to(spoken_turn_prompt(spoken_lines))
        except ConversationTurnError as error:
            logger.warning("agent turn failed: %s", error)
            reply = FAILED_TURN_APOLOGY
        if reply_worth_speaking(reply):
            await speak(reply)


async def conduct_call():
    bridge = BridgeControl(os.environ["VOICE_BRIDGE_CONTROL_SOCKET"])
    agent = os.environ.get("VOICE_CONDUCTOR_AGENT")
    conversation = (
        A2AConversation(await live_peer(agent))
        if agent
        else HermesConversation(
            os.environ["VOICE_CONDUCTOR_HERMES"], os.environ["VOICE_CONDUCTOR_PROFILE"]
        )
    )
    router = ConversationRouter(conversation)
    socket_path = Path(os.environ["VOICE_CONDUCTOR_CONTROL_SOCKET"])
    server = await asyncio.start_unix_server(router.serve_connection, path=socket_path)
    socket_path.chmod(0o600)
    pending_lines = asyncio.Queue(maxsize=PENDING_LINE_LIMIT)
    collection = asyncio.create_task(
        collect_spoken_lines(bridge.spoken_lines(), pending_lines)
    )
    answering = asyncio.create_task(
        answer_spoken_lines(pending_lines, router.reply_to, bridge.speak)
    )
    stop_requested = asyncio.Event()
    loop = asyncio.get_running_loop()
    for stop_signal in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(stop_signal, stop_requested.set)
    stopping = asyncio.create_task(stop_requested.wait())
    async with server:
        try:
            finished, _ = await asyncio.wait(
                {collection, answering, stopping}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in finished:
                task.result()
            if stopping not in finished:
                raise ConnectionError("bridge_closed_the_transcript")
        finally:
            answering.cancel()
            collection.cancel()
            stopping.cancel()
            await asyncio.gather(
                answering, collection, stopping, return_exceptions=True
            )


def main():
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(conduct_call())


if __name__ == "__main__":
    main()
