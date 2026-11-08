import argparse
import subprocess
import sys

import conversation_effects
import conversation_state
import listener
import utterances
from conversation_state import ConversationAction, ConversationCommand

HEAR_WAIT_SECONDS = 100


def parse_arguments():
    parser = argparse.ArgumentParser(prog="avatar-talk")
    commands = parser.add_subparsers(dest="action", required=True)
    opening = commands.add_parser("open")
    opening.add_argument("--language")
    opening.add_argument("--character")
    speaking = commands.add_parser("say")
    asking = commands.add_parser("ask")
    for parser_with_speech in (speaking, asking):
        parser_with_speech.add_argument("text")
        parser_with_speech.add_argument("emotion", nargs="?", default="neutral")
        parser_with_speech.add_argument("--voice")
    hearing = commands.add_parser("hear")
    for parser_with_wait in (asking, hearing):
        parser_with_wait.add_argument("--wait", type=float, default=HEAR_WAIT_SECONDS)
    for name in ("follow", "status", "show", "hide", "close"):
        commands.add_parser(name)
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    actions = {
        ConversationAction.BRING_UP: conversation_effects.open_conversation,
        ConversationAction.KEEP_OPEN: conversation_effects.keep_conversation_open,
        ConversationAction.TEAR_DOWN: conversation_effects.close_conversation,
        ConversationAction.LEAVE_MEETING: conversation_effects.leave_meeting,
        ConversationAction.ASK: conversation_effects.ask,
        ConversationAction.HEAR: conversation_effects.hear,
        ConversationAction.FOLLOW: conversation_effects.follow,
        ConversationAction.SAY: conversation_effects.say,
        ConversationAction.SHOW: conversation_effects.show_window,
        ConversationAction.HIDE: conversation_effects.hide_window,
        ConversationAction.REPORT: conversation_effects.status,
        ConversationAction.REFUSE_CLOSED: conversation_effects.refuse_closed,
        ConversationAction.REFUSE_MEETING: conversation_effects.refuse_meeting,
    }
    try:
        directory = listener.runtime_directory()
        command = ConversationCommand(arguments.action)
        decision = conversation_state.decide(
            conversation_state.observe(directory), command
        )
        actions[decision](arguments, directory)
    except (
        utterances.ConversationClosed,
        subprocess.SubprocessError,
        RuntimeError,
        TimeoutError,
        ValueError,
    ) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
