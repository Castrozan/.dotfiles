import asyncio
import json
import re
import time
from dataclasses import dataclass

import remote_agent

ANSWER_MARKER = "⏺"
ANSWER_TAG = "LIVE-ANSWER"
SENDER = "avatar live voice"
ANSWER_DEADLINE_SECONDS = 300
POLL_SECONDS = 2
STILL_WORKING_SECONDS = 30
COMMAND_TIMEOUT_SECONDS = 20
TERMINAL_STATES = frozenset({"completed", "canceled", "failed"})
STILL_WORKING = "The agent is still working on that and has not answered yet."
NO_ANSWER_IN_TIME = (
    f"The agent gave no answer within {ANSWER_DEADLINE_SECONDS // 60} minutes; "
    "it may still be busy, so ask again in a while."
)

BRIEF = (
    "[avatar-live] Lucas asked this by voice in the open live avatar conversation, and the "
    "live voice will read your answer aloud to him: {request} -- Do the work, then begin "
    "your closing message with {tag} and a colon, followed by one short plain spoken "
    "sentence that answers him, in the language he used, with no markdown, code or file "
    "paths. Answer that way at once even while background work of yours still runs."
)


@dataclass(frozen=True)
class AgentReport:
    text: str
    seconds: float
    final: bool


class AgentUnreachable(Exception):
    pass


def answer_tag(number):
    return f"{ANSWER_TAG}-{number}"


def spoken_answer(output):
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    answers = [
        line.removeprefix(ANSWER_MARKER).strip()
        for line in lines
        if line.startswith(ANSWER_MARKER)
    ]
    return answers[-1] if answers else None, lines[-1] if lines else ""


def tagged_answer(output, tag):
    pattern = re.compile(rf"^\W?\s*{re.escape(tag)}:\s*(\S.*)$")
    matches = [pattern.match(line.strip()) for line in output.splitlines()]
    answers = [match.group(1).strip() for match in matches if match]
    return answers[0] if answers else None


def finished_answer(task):
    answer, _ = spoken_answer(task.get("output") or "")
    if task.get("state") == "completed" and answer:
        return answer
    reason = task.get("errorMessage") or f"its task ended {task.get('state')}"
    return f"The agent could not finish that: {reason}"


def answer_in(task, tag):
    tagged = tagged_answer(task.get("output") or "", tag)
    if tagged:
        return tagged
    if task.get("state") in TERMINAL_STATES:
        return finished_answer(task)
    return None


def a2a_command(holder, arguments):
    return remote_agent.on_host(holder.host, ["a2a", *arguments])


def send_command(holder, request, tag):
    brief = BRIEF.format(request=request, tag=tag)
    return a2a_command(holder, ["send", "--sender", SENDER, holder.pane, brief])


def status_command(holder, task_id):
    return a2a_command(holder, ["status", holder.pane, task_id])


async def stopped(process):
    if process.returncode is None:
        process.kill()
        await process.wait()


async def run_bounded(command):
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        output, _ = await asyncio.wait_for(
            process.communicate(), COMMAND_TIMEOUT_SECONDS
        )
    except TimeoutError:
        return None, f"a2a gave no reply within {COMMAND_TIMEOUT_SECONDS} s"
    finally:
        await stopped(process)
    return process.returncode, output.decode()


async def submitted_task(holder, request, tag):
    code, output = await run_bounded(send_command(holder, request, tag))
    lines = output.strip().splitlines()
    if code != 0 or not lines:
        raise AgentUnreachable(lines[-1] if lines else f"exit {code}")
    return lines[-1].strip()


async def task_now(holder, task_id):
    code, output = await run_bounded(status_command(holder, task_id))
    if code != 0:
        return {}
    try:
        task = json.loads(output)
    except ValueError:
        return {}
    return task if isinstance(task, dict) else {}


async def progress_until_answered(holder, task_id, tag):
    deadline = time.monotonic() + ANSWER_DEADLINE_SECONDS
    next_still_working = time.monotonic() + STILL_WORKING_SECONDS
    while time.monotonic() < deadline:
        await asyncio.sleep(POLL_SECONDS)
        answer = answer_in(await task_now(holder, task_id), tag)
        if answer:
            yield answer, True
            return
        if time.monotonic() >= next_still_working:
            next_still_working += STILL_WORKING_SECONDS
            yield STILL_WORKING, False
    yield NO_ANSWER_IN_TIME, True


async def reports(holder, request, tag):
    try:
        task_id = await submitted_task(holder, request, tag)
    except AgentUnreachable as failure:
        yield f"The agent could not finish that: {failure}", True
        return
    async for report in progress_until_answered(holder, task_id, tag):
        yield report


async def ask_agent(holder, request, number):
    started = time.monotonic()
    async for text, final in reports(holder, request, answer_tag(number)):
        yield AgentReport(text, round(time.monotonic() - started, 1), final)
