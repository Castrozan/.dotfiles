import os
import pathlib
import subprocess

CHARACTERS_ENVIRONMENT_VARIABLE = "AVATAR_SERVANT_CHARACTERS"
SWITCH_TIMEOUT_SECONDS = 30
SEPARATOR = " | "


def listed_characters():
    path = os.environ.get(CHARACTERS_ENVIRONMENT_VARIABLE)
    if not path:
        return {}
    try:
        lines = pathlib.Path(path).read_text().splitlines()
    except OSError:
        return {}
    pairs = (line.partition(SEPARATOR) for line in lines)
    return {
        name: character.strip() for name, separator, character in pairs if separator
    }


def character_for(servant):
    return listed_characters().get(servant)


def show(character):
    if character is None:
        return
    try:
        subprocess.run(
            ["avatar-command", "character", character],
            stdout=subprocess.DEVNULL,
            check=True,
            timeout=SWITCH_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return


def show_for(servant):
    show(character_for(servant))
