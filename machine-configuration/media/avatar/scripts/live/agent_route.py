import asyncio
import time
from dataclasses import dataclass

import remote_agent

ANSWER_MARKER = "⏺"
SENDER = "avatar live voice"
TIMEOUT_SECONDS = 300

BRIEF = (
    "[avatar-live] Lucas asked this by voice in the open live avatar conversation, and the "
    "live voice will read your answer aloud to him: {request} -- Do the work, then end your turn "
    "with one short plain spoken sentence that answers him, in the language he used, with no "
    "markdown, code or file paths."
)


@dataclass(frozen=True)
class AgentAnswer:
    text: str
    seconds: float
    succeeded: bool


def spoken_answer(output):
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    answers = [
        line.removeprefix(ANSWER_MARKER).strip()
        for line in lines
        if line.startswith(ANSWER_MARKER)
    ]
    return answers[-1] if answers else None, lines[-1] if lines else ""


def ask_command(holder, request):
    return remote_agent.on_host(
        holder.host,
        [
            "a2a",
            "ask",
            "--sender",
            SENDER,
            "--timeout-seconds",
            str(TIMEOUT_SECONDS),
            holder.pane,
            BRIEF.format(request=request),
        ],
    )


async def ask_agent(holder, request):
    started = time.monotonic()
    process = await asyncio.create_subprocess_exec(
        *ask_command(holder, request),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    output, _ = await process.communicate()
    seconds = round(time.monotonic() - started, 1)
    answer, last_line = spoken_answer(output.decode())
    if process.returncode == 0 and answer:
        return AgentAnswer(answer, seconds, True)
    reason = last_line or f"exit {process.returncode}"
    return AgentAnswer(f"The agent could not finish that: {reason}", seconds, False)
