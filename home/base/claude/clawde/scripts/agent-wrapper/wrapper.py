import argparse
import json
import signal
import sys
import time

from restart_scheduling import (
    INITIAL_RESTART_DELAY_SECONDS,
    MAXIMUM_RESTART_DELAY_SECONDS,
    is_within_active_hours,
    seconds_until_active_hours_start,
    should_reset_backoff,
    should_rotate_session,
)
from session_watchdog import run_launch_command_once, terminate_process_tree


class RedeploySignalState:
    def __init__(self) -> None:
        self.resume_requested = False
        self.current_child_process_id: int | None = None


redeploy_signal_state = RedeploySignalState()


def register_current_child_process_id(child_process_id: int | None) -> None:
    redeploy_signal_state.current_child_process_id = child_process_id


def install_exit_signal_handlers() -> None:
    def terminate_cleanly(_signal_number: int, _frame_object) -> None:
        sys.exit(0)

    for signal_number in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(signal_number, terminate_cleanly)


def request_resume_restart_now() -> None:
    redeploy_signal_state.resume_requested = True
    child_process_id = redeploy_signal_state.current_child_process_id
    if child_process_id is not None:
        terminate_process_tree(child_process_id)


def install_redeploy_signal_handler() -> None:
    def handle_redeploy_signal(_signal_number: int, _frame_object) -> None:
        request_resume_restart_now()

    signal.signal(signal.SIGUSR1, handle_redeploy_signal)


def build_tmux_target(tmux_session: str | None, agent_name: str) -> str | None:
    if not tmux_session:
        return None
    return f"{tmux_session}:{agent_name}"


def supervise_agent_forever(
    agent_name: str,
    launch_command: str,
    heartbeat_driver_argv: list[str] | None,
    active_hours_start: int | None,
    active_hours_end: int | None,
    daily_session_rotation: bool,
    tmux_target: str | None,
) -> None:
    restart_delay_seconds = INITIAL_RESTART_DELAY_SECONDS
    last_fresh_start_date: str | None = None

    while True:
        if not is_within_active_hours(active_hours_start, active_hours_end):
            sleep_seconds = seconds_until_active_hours_start(active_hours_start)
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Agent {agent_name} outside active hours. "
                f"Sleeping {sleep_seconds} seconds until {active_hours_start}:00...",
                flush=True,
            )
            time.sleep(sleep_seconds)
            last_fresh_start_date = None
            continue

        if should_rotate_session(daily_session_rotation, last_fresh_start_date):
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Agent {agent_name} daily session rotation. Starting fresh.",
                flush=True,
            )
            last_fresh_start_date = None

        if last_fresh_start_date is None:
            last_fresh_start_date = time.strftime("%Y-%m-%d")

        resume_continue = redeploy_signal_state.resume_requested
        redeploy_signal_state.resume_requested = False
        runtime_seconds, was_stuck_kill = run_launch_command_once(
            launch_command,
            heartbeat_driver_argv,
            tmux_target,
            resume_continue=resume_continue,
            register_child_pid=register_current_child_process_id,
        )

        if not is_within_active_hours(active_hours_start, active_hours_end):
            continue

        if should_reset_backoff(runtime_seconds, was_stuck_kill):
            restart_delay_seconds = INITIAL_RESTART_DELAY_SECONDS

        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"Agent {agent_name} exited after {int(runtime_seconds)} seconds. "
            f"Restarting in {restart_delay_seconds} seconds...",
            flush=True,
        )
        time.sleep(restart_delay_seconds)

        restart_delay_seconds = min(
            restart_delay_seconds * 2, MAXIMUM_RESTART_DELAY_SECONDS
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clawde-agent-wrapper",
        description="Run a clawde agent launch command in a restart loop with exponential backoff",
    )
    parser.add_argument(
        "--agent-name",
        required=True,
        help="Agent name used in restart log messages and as the tmux window name",
    )
    parser.add_argument(
        "--launch-command",
        required=True,
        help="Shell command that starts the agent (runs under bash -c)",
    )
    parser.add_argument(
        "--heartbeat-driver-argv",
        default=None,
        help="JSON-encoded argv list for the heartbeat driver process",
    )
    parser.add_argument(
        "--active-hours-start",
        type=int,
        default=None,
        help="Hour (0-23) when agent becomes active",
    )
    parser.add_argument(
        "--active-hours-end",
        type=int,
        default=None,
        help="Hour (0-23) when agent goes dormant",
    )
    parser.add_argument(
        "--daily-session-rotation",
        action="store_true",
        default=False,
        help="Enable once-per-day forced session restart",
    )
    parser.add_argument(
        "--tmux-session",
        default=None,
        help="tmux session holding the agent window; enables the stuck-session watchdog",
    )
    return parser.parse_args()


def main() -> None:
    install_exit_signal_handlers()
    install_redeploy_signal_handler()
    arguments = parse_arguments()

    heartbeat_driver_argv = None
    if arguments.heartbeat_driver_argv:
        heartbeat_driver_argv = json.loads(arguments.heartbeat_driver_argv)

    supervise_agent_forever(
        arguments.agent_name,
        arguments.launch_command,
        heartbeat_driver_argv,
        arguments.active_hours_start,
        arguments.active_hours_end,
        arguments.daily_session_rotation,
        build_tmux_target(arguments.tmux_session, arguments.agent_name),
    )


if __name__ == "__main__":
    main()
