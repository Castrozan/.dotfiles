import argparse

import remote_agent
from conversation_seat import Seat

HEAR_WAIT_SECONDS = 100


def parse_arguments(arguments=None):
    parser = argparse.ArgumentParser(prog="avatar-talk")
    commands = parser.add_subparsers(dest="action", required=True)
    opening = commands.add_parser("open")
    opening.add_argument("--language")
    opening.add_argument("--character")
    opening.add_argument("--live", action="store_true")
    opening.add_argument("--holder", metavar="HERMES_PROFILE")
    opening.add_argument("--seat", choices=list(Seat), type=Seat)
    opening.add_argument("--agent", type=remote_agent.parse, metavar="HOST:PANE")
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
    return parser.parse_args(arguments)
