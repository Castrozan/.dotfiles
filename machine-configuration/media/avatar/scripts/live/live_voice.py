import asyncio
import json
import os
import pathlib
import time

import conversation_addressee
import servant_character

DEFAULT_VOICE = "marin"
VOICES_ENVIRONMENT_VARIABLE = "AVATAR_CHARACTER_VOICES"
HOLDER_WAIT_SECONDS = 15
HOLDER_POLL_SECONDS = 0.1


def live_voices_by_character():
    path = os.environ.get(VOICES_ENVIRONMENT_VARIABLE)
    if not path:
        return {}
    try:
        characters = json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError):
        return {}
    return {
        character["name"]: character["liveVoice"]
        for character in characters
        if "liveVoice" in character
    }


def voice_for(servant):
    character = servant_character.character_for(servant)
    return live_voices_by_character().get(character, DEFAULT_VOICE)


def holder_voice(directory):
    holder = conversation_addressee.current(directory)
    return voice_for(holder.servant) if holder else None


async def voice_of_the_room_holder(directory):
    deadline = time.monotonic() + HOLDER_WAIT_SECONDS
    holder = conversation_addressee.current(directory)
    while holder is None and time.monotonic() < deadline:
        await asyncio.sleep(HOLDER_POLL_SECONDS)
        holder = conversation_addressee.current(directory)
    return voice_for(holder.servant) if holder else DEFAULT_VOICE
