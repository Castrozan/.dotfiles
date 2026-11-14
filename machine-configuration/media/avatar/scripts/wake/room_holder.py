import conversation_addressee
import servant_character


def give_the_room_to(directory, addressee):
    previous = conversation_addressee.current(directory)
    conversation_addressee.hand_to(directory, addressee)
    if previous is None or previous.servant != addressee.servant:
        servant_character.show_for(addressee.servant)
