"""Standalone thin client; imports no harness or local session-control code."""

import argparse
import sys

from .cli import add_parser


def main():
    parser = argparse.ArgumentParser(prog="dot-fleet")
    add_parser(parser.add_subparsers(dest="command", required=True))
    arguments = parser.parse_args(["fleet", *sys.argv[1:]])
    return arguments.handler(arguments)


if __name__ == "__main__":
    sys.exit(main())
