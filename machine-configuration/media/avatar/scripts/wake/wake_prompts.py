from listener_session import ListenerPurpose

DESK_REPLY = (
    "speak with avatar-talk say, and hear the reply through avatar-talk follow in a "
    "background watcher. When the room dismisses you, such as 'you can go now', say "
    "a short goodbye and run avatar-talk close, which hands the room back to the wake."
)
SETTINGS = {
    None: f"An avatar conversation is opening: {DESK_REPLY}",
    ListenerPurpose.CONVERSATION: (
        f"The open avatar conversation now listens for you: {DESK_REPLY}"
    ),
    ListenerPurpose.MEETING: (
        "You now hold the floor of the meeting the avatar transcribes: answer aloud "
        "with avatar-command speak, which the meeting hears, and read it through "
        "avatar-listen follow in a background watcher."
    ),
}


def spoken_prompt(message, purpose):
    return (
        f"[wake] Voice from the room, speaker not verified: {message} "
        f"{SETTINGS[purpose]}"
    )
