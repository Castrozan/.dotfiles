import dataclasses

import conversation_addressee
import listener_session
import room_holder
import servant_character
import utterances
from conversation_addressee import Addressee

CONFIGURATION_KEY = "default_holder"


@dataclasses.dataclass(frozen=True)
class DefaultHolder:
    profile: str
    character: str | None = None

    @property
    def pane(self):
        return conversation_addressee.hermes_pane(self.profile)

    @property
    def servant(self):
        return self.profile.capitalize()


def listener_settings(arguments):
    profile = getattr(arguments, "holder", None)
    if not profile:
        return {}
    holder = DefaultHolder(profile, arguments.character)
    return {CONFIGURATION_KEY: dataclasses.asdict(holder)}


def configured(directory):
    record = listener_session.read_configuration(directory).get(CONFIGURATION_KEY)
    return DefaultHolder(**record) if record else None


def take_the_floor(directory, holder):
    heard_through = utterances.last_heard(directory)
    room_holder.give_the_room_to(
        directory, Addressee(holder.pane, holder.servant, heard_through)
    )
    servant_character.show(holder.character)


def holds_the_floor(directory, pane):
    current = conversation_addressee.current(directory)
    return current is not None and current.pane == pane


def floor_returns_to(directory, pane):
    holder = configured(directory)
    if holder is None or pane == holder.pane:
        return None
    return holder if holds_the_floor(directory, pane) else None
