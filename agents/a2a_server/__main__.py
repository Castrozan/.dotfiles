import argparse
import re
import sys

from .a2a_server import run_a2a_server_blocking
from .agent_card import build_agent_card_from_environment
from .backends.base import AgentBackend
from .backends.herdr_backend import HerdrAttachedAgentBackend
from .backends.subprocess_backend import SubprocessAgentBackend


def parse_command_line_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="a2a-server",
        description=(
            "HTTP server that exposes a single CLI agent as an A2A peer. "
            "Wraps either a herdr-attached agent (default) or a subprocess agent."
        ),
    )
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--agent-description", default="A CLI agent exposed via A2A.")
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, required=True)
    parser.add_argument(
        "--public-endpoint-url",
        default=None,
        help="URL advertised in the Agent Card. Defaults to http://<listen-host>:<listen-port>.",
    )
    parser.add_argument(
        "--backend-type",
        choices=["herdr", "subprocess"],
        required=True,
    )
    parser.add_argument("--herdr-pane", default=None)
    parser.add_argument(
        "--herdr-meaningful-line-pattern",
        default=None,
        help=(
            "Optional regex. When set, only pane lines matching this pattern count as "
            "meaningful new output; status-line/spinner redraws are ignored so the idle "
            "auto-complete timeout actually fires. For claude-code TUI, use '^⏺ '."
        ),
    )
    parser.add_argument(
        "--subprocess-command",
        nargs="+",
        default=None,
        help="argv for the subprocess backend (everything after this flag is the command)",
    )
    return parser.parse_args()


def construct_backend_from_arguments(arguments: argparse.Namespace) -> AgentBackend:
    if arguments.backend_type == "herdr":
        if not arguments.herdr_pane:
            print(
                "error: --herdr-pane is required for backend-type=herdr",
                file=sys.stderr,
            )
            sys.exit(2)
        compiled_meaningful_line_pattern = (
            re.compile(arguments.herdr_meaningful_line_pattern)
            if arguments.herdr_meaningful_line_pattern
            else None
        )
        return HerdrAttachedAgentBackend(
            herdr_pane_id=arguments.herdr_pane,
            meaningful_line_pattern=compiled_meaningful_line_pattern,
        )
    if not arguments.subprocess_command:
        print(
            "error: --subprocess-command is required for backend-type=subprocess",
            file=sys.stderr,
        )
        sys.exit(2)
    return SubprocessAgentBackend(command_argv=arguments.subprocess_command)


def main() -> None:
    arguments = parse_command_line_arguments()
    endpoint_url = (
        arguments.public_endpoint_url
        or f"http://{arguments.listen_host}:{arguments.listen_port}"
    )
    agent_card = build_agent_card_from_environment(
        agent_name=arguments.agent_name,
        description=arguments.agent_description,
        endpoint_url=endpoint_url,
    )
    backend = construct_backend_from_arguments(arguments)
    run_a2a_server_blocking(
        host=arguments.listen_host,
        port=arguments.listen_port,
        agent_card=agent_card,
        agent_backend=backend,
    )


if __name__ == "__main__":
    main()
