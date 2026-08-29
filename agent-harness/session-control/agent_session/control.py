import argparse
import os

from . import harness, relaunch, restart_lock
from .processes import (
    clawde_wrapper_is_ancestor_of,
    process_is_descendant_of,
    terminate_agent_session,
)
from .herdr_session import herdr_pane_agent_session_identifier
from .relaunch_transport import herdr_pane_foreground_process_identifiers

multiplexer_context_from_environment = relaunch.multiplexer_context_from_environment
launch_restart_launcher = relaunch.launch_restart_launcher


def starting_process_identifier() -> int:
    return os.getppid()


def agent_session_from_current_process() -> tuple[int, str, str] | None:
    return harness.find_agent_session(starting_process_identifier())


def herdr_pane_contains_agent_session(
    pane_identifier: str, agent_session_process_identifier: int
) -> bool:
    foreground_process_identifiers = herdr_pane_foreground_process_identifiers(
        pane_identifier
    )
    if foreground_process_identifiers is None:
        return False
    return any(
        process_is_descendant_of(
            foreground_process_identifier,
            agent_session_process_identifier,
        )
        for foreground_process_identifier in foreground_process_identifiers
    )


def exit_current_agent_session(arguments: argparse.Namespace) -> int:
    agent_session = agent_session_from_current_process()
    if agent_session is None:
        print(
            "No Claude, Codex, or OpenCode process was found among this command's ancestors."
        )
        return 1
    process_identifier, harness_name, _command_line = agent_session
    print(f"Harness: {harness_name}\nPID: {process_identifier}")
    if arguments.print_target:
        return 0
    terminate_agent_session(process_identifier)
    return 0


def restart_current_agent_session(_arguments: argparse.Namespace) -> int:
    if os.environ.get("CLAWDE_AGENT_NAME") or clawde_wrapper_is_ancestor_of(
        starting_process_identifier()
    ):
        print("Clawde-managed sessions must be relaunched by their wrapper.")
        return 1
    agent_session = agent_session_from_current_process()
    if agent_session is None:
        print(
            "No Claude, Codex, or OpenCode process was found among this command's ancestors."
        )
        return 1
    multiplexer_context = multiplexer_context_from_environment()
    if multiplexer_context is None:
        print(
            "Restart requires the current Herdr pane so the harness can be relaunched safely."
        )
        return 1
    process_identifier, harness_name, command_line = agent_session
    multiplexer_name, pane_identifier = multiplexer_context
    if not herdr_pane_contains_agent_session(pane_identifier, process_identifier):
        print("Restart target pane does not contain the current harness process.")
        return 1
    session_identifier = harness.session_identifier_from_command(
        harness_name, command_line
    ) or herdr_pane_agent_session_identifier(pane_identifier, harness_name)
    if session_identifier is None:
        print("Restart could not resolve the current Herdr pane's agent session ID.")
        return 1
    acquired_restart_lock = restart_lock.acquire_restart_lock(process_identifier)
    if acquired_restart_lock is None:
        print("A restart is already pending for the current harness process.")
        return 1
    resume_command = harness.resume_command_for(harness_name, session_identifier)
    restart_launcher_process_identifier = launch_restart_launcher(
        process_identifier,
        multiplexer_name,
        pane_identifier,
        resume_command,
        acquired_restart_lock,
    )
    if restart_launcher_process_identifier is None:
        restart_lock.release_restart_lock(acquired_restart_lock)
        print("Restart launcher could not prepare the target pane.")
        return 1
    terminate_agent_session(
        process_identifier,
        frozenset({os.getpid(), restart_launcher_process_identifier}),
    )
    return 0


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-session")
    subcommands = parser.add_subparsers(dest="command", required=True)

    exit_parser = subcommands.add_parser("exit")
    exit_parser.add_argument("--print-target", action="store_true")
    exit_parser.set_defaults(handler=exit_current_agent_session)

    restart_parser = subcommands.add_parser("restart")
    restart_parser.set_defaults(handler=restart_current_agent_session)

    launch_parser = subcommands.add_parser("launch")
    launch_parser.add_argument("--process-identifier", type=int, required=True)
    launch_parser.add_argument("--multiplexer-name", required=True)
    launch_parser.add_argument("--pane-identifier", required=True)
    launch_parser.add_argument("--resume-command", required=True)
    launch_parser.add_argument("--restart-lock-path", required=True)
    launch_parser.add_argument("--restart-lock-owner-token", required=True)
    launch_parser.add_argument(
        "--restart-launcher-ready-file-descriptor", type=int, required=True
    )
    launch_parser.set_defaults(handler=relaunch.relaunch_after_exit)

    return parser


def main() -> int:
    arguments = build_argument_parser().parse_args()
    return arguments.handler(arguments)
