import asyncio
import json
import logging
import os
import sys
from datetime import date

CONTROL_CONNECT_RETRY_SECONDS = 1
HERMES_TURN_DEADLINE_SECONDS = 120
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


class HermesTurnError(Exception):
    pass


def spoken_turn_prompt(spoken_lines):
    return f"{SPOKEN_CALL_INSTRUCTION}\n\nLucas: {' '.join(spoken_lines)}"


def reply_worth_speaking(reply):
    return bool(reply) and reply.strip(" .\n") != STAY_SILENT_REPLY


def final_reply_from_turn_events(turn_output):
    for line in reversed(turn_output.splitlines()):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            return event.get("text", "")
    raise HermesTurnError("turn_produced_no_result")


class HermesConversation:
    def __init__(self, hermes_executable, profile):
        self._hermes_executable = hermes_executable
        self._profile = profile

    async def reply_to(self, prompt):
        process = await asyncio.create_subprocess_exec(
            self._hermes_executable,
            "-p",
            self._profile,
            "chat",
            "--query",
            prompt,
            "--oneshot",
            "--continue",
            f"voice-call-{date.today().isoformat()}",
            "--create-if-missing",
            "--reasoning",
            "low",
            "--source",
            "tool",
            "--format",
            "stream-json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            turn_output, _ = await asyncio.wait_for(
                process.communicate(), HERMES_TURN_DEADLINE_SECONDS
            )
        except TimeoutError as error:
            process.kill()
            raise HermesTurnError("turn_timed_out") from error
        if process.returncode != 0:
            raise HermesTurnError(f"turn_exited_{process.returncode}")
        return final_reply_from_turn_events(turn_output.decode())


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
        while line := await reader.readline():
            text = json.loads(line).get("text")
            if text:
                yield text

    async def speak(self, text):
        reader, writer = await self._connected()
        request = {"command": "speak", "text": text, "language": SPEECH_LANGUAGE}
        writer.write(json.dumps(request).encode() + b"\n")
        await writer.drain()
        reply = await reader.readline()
        writer.close()
        if reply and "error" in json.loads(reply):
            logger.warning("speech rejected: %s", json.loads(reply)["error"])


def drained_spoken_lines(first_line, pending_lines):
    spoken_lines = [first_line]
    while not pending_lines.empty():
        spoken_lines.append(pending_lines.get_nowait())
    return spoken_lines


async def collect_spoken_lines(transcript_lines, pending_lines):
    async for text in transcript_lines:
        pending_lines.put_nowait(text)


async def answer_spoken_lines(pending_lines, reply_to, speak):
    while True:
        spoken_lines = drained_spoken_lines(await pending_lines.get(), pending_lines)
        try:
            reply = await reply_to(spoken_turn_prompt(spoken_lines))
        except HermesTurnError as error:
            logger.warning("hermes turn failed: %s", error)
            reply = FAILED_TURN_APOLOGY
        if reply_worth_speaking(reply):
            await speak(reply)


async def conduct_call():
    bridge = BridgeControl(os.environ["VOICE_BRIDGE_CONTROL_SOCKET"])
    conversation = HermesConversation(
        os.environ["VOICE_CONDUCTOR_HERMES"], os.environ["VOICE_CONDUCTOR_PROFILE"]
    )
    pending_lines = asyncio.Queue()
    collection = asyncio.create_task(
        collect_spoken_lines(bridge.spoken_lines(), pending_lines)
    )
    answering = asyncio.create_task(
        answer_spoken_lines(pending_lines, conversation.reply_to, bridge.speak)
    )
    await asyncio.wait({collection, answering}, return_when=asyncio.FIRST_COMPLETED)
    answering.cancel()
    collection.cancel()


def main():
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(conduct_call())
    sys.exit("bridge closed the transcript")


if __name__ == "__main__":
    main()
