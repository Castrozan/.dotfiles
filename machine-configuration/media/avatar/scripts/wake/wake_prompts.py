import os

import remote_agent
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

REMOTE_ROOM = (
    "the room is on machine {room}, so start every avatar command with "
    "AVATAR_ROOM={room}, which sends it there as you: "
)
REMOTE_DESK_REPLY = (
    REMOTE_ROOM
    + 'speak with {reach} avatar-talk say "...", and hear the reply through {reach} '
    "avatar-talk follow in a background watcher. When the room dismisses you, such "
    "as 'you can go now', say a short goodbye and run {reach} avatar-talk close, "
    "which hands the room back to the wake."
)
REMOTE_SETTINGS = {
    None: f"An avatar conversation is opening: {REMOTE_DESK_REPLY}",
    ListenerPurpose.CONVERSATION: (
        f"The open avatar conversation now listens for you: {REMOTE_DESK_REPLY}"
    ),
    ListenerPurpose.MEETING: (
        "You now hold the floor of the meeting the avatar transcribes, and "
        + REMOTE_ROOM
        + 'answer aloud with {reach} avatar-talk say "...", which the meeting hears, '
        "and read it through {reach} avatar-talk follow in a background watcher."
    ),
}


def room_name():
    return os.environ[remote_agent.HOST_ENVIRONMENT_VARIABLE]


def setting_for(purpose, session):
    if session is None or session.host is None:
        return SETTINGS[purpose]
    room = room_name()
    reach = f"AVATAR_ROOM={room}"
    return REMOTE_SETTINGS[purpose].format(room=room, reach=reach)


def spoken_prompt(message, purpose, session=None):
    return (
        f"[wake] Voice from the room, speaker not verified: {message} "
        f"{setting_for(purpose, session)}"
    )


def deliver(boundaries, dry_run, match, purpose):
    session = match.session
    target = f"{session.servant} at {session.pane}"
    if dry_run:
        boundaries.report(f"would wake {target}: {match.message}")
        return False
    boundaries.report(f"wake {target}")
    text = spoken_prompt(match.message, purpose, session)
    if not boundaries.prompt_now(session.pane, text, session.host):
        boundaries.notify_at_idle(session.pane, text, session.host)
    return True
