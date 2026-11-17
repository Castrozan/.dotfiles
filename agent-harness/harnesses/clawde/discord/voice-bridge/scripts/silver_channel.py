import asyncio
import json
import logging
import subprocess

HOLDER_UNIT = "silver-voice-holder.service"
COMMAND_TIMEOUT_SECONDS = 15

logger = logging.getLogger(__name__)


def run_command(arguments):
    try:
        return subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def avatar_conversation_is_closed(run=run_command):
    status = run(["avatar-talk", "status"])
    if status is None or status.returncode != 0:
        return False
    try:
        return json.loads(status.stdout).get("open") is False
    except (ValueError, AttributeError):
        return False


def start_holder(run=run_command):
    if not avatar_conversation_is_closed(run):
        return
    started = run(["systemctl", "--user", "start", "--no-block", HOLDER_UNIT])
    if started is None or started.returncode != 0:
        logger.warning("the silver voice holder did not start")


class SilverChannel:
    def __init__(self, guild_id, channel_name, run=run_command):
        self.guild_id = guild_id
        self.channel_name = channel_name
        self.run = run

    def is_entered(self, channel):
        return (
            channel is not None
            and channel.guild.id == self.guild_id
            and channel.name == self.channel_name
        )

    async def listener_moved_to(self, channel):
        if self.is_entered(channel):
            await asyncio.to_thread(start_holder, self.run)
