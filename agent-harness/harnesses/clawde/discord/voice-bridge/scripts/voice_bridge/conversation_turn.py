import asyncio
import os
import signal

TURN_DEADLINE_SECONDS = 120


class ConversationTurnError(Exception):
    pass


async def start_agent_command(arguments):
    try:
        return await asyncio.create_subprocess_exec(
            *arguments,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as error:
        raise ConversationTurnError("agent_command_unavailable") from error


async def stop_agent_command(process):
    if process.returncode is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    await process.wait()


async def command_output(arguments, deadline_seconds=TURN_DEADLINE_SECONDS):
    process = await start_agent_command(arguments)
    try:
        output, _ = await asyncio.wait_for(process.communicate(), deadline_seconds)
    except asyncio.CancelledError:
        await stop_agent_command(process)
        raise
    except TimeoutError as error:
        await stop_agent_command(process)
        raise ConversationTurnError("turn_timed_out") from error
    if process.returncode != 0:
        raise ConversationTurnError(f"agent_command_exited_{process.returncode}")
    return output
