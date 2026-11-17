import conversation_addressee
import servant_character
from conversation_addressee import Addressee


def addressee_of(session, heard_through):
    return Addressee(session.pane, session.servant, heard_through, session.host)


def give_the_room_to(directory, addressee):
    previous = conversation_addressee.current(directory)
    conversation_addressee.hand_to(directory, addressee)
    if previous is None or previous.servant != addressee.servant:
        servant_character.show_for(addressee.servant)
