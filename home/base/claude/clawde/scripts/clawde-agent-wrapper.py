import argparse
import datetime
import json
import signal
import subprocess
import sys
import time

INITIAL_RESTART_DELAY_SECONDS = 10
MAXIMUM_RESTART_DELAY_SECONDS = 300
STABLE_RUNTIME_THRESHOLD_SECONDS = 60


def install_exit_signal_handlers() -> None:
    def terminate_cleanly(_signal_number: int, _frame_object) -> None:
        sys.exit(0)

    for signal_number in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(signal_number, terminate_cleanly)


def is_within_active_hours(
    active_hours_start: int | None,
    active_hours_end: int | None,
    now: datetime.datetime | None = None,
) -> bool:
    if active_hours_start is None:
        return True
    if now is None:
        now = datetime.datetime.now()
    current_hour = now.hour
    if active_hours_start <= active_hours_end:
        return active_hours_start <= current_hour < active_hours_end
    return current_hour >= active_hours_start or current_hour < active_hours_end


def seconds_until_active_hours_start(
    active_hours_start: int,
    now: datetime.datetime | None = None,
) -> int:
    if now is None:
        now = datetime.datetime.now()
    target = now.replace(hour=active_hours_start, minute=0, second=0, microsecond=0)
    if target <= now and now.hour != active_hours_start:
        target += datetime.timedelta(days=1)
    return max(1, int((target - now).total_seconds()))


def should_rotate_session(
    daily_session_rotation: bool, last_fresh_start_date: str | None
) -> bool:
    if not daily_session_rotation:
        return False
    if last_fresh_start_date is None:
        return False
    today = time.strftime("%Y-%m-%d")
    return last_fresh_start_date != today


def run_launch_command_once(
    launch_command: str, heartbeat_driver_argv: list[str] | None
) -> float:
    start_time = time.time()
    driver_process = (
        subprocess.Popen(heartbeat_driver_argv) if heartbeat_driver_argv else None
    )
    try:
        subprocess.run(["bash", "-c", launch_command], check=False)
    finally:
        if driver_process is not None:
            driver_process.terminate()
            try:
                driver_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                driver_process.kill()
    return time.time() - start_time


def supervise_agent_forever(
    agent_name: str,
    launch_command: str,
    heartbeat_driver_argv: list[str] | None,
    active_hours_start: int | None,
    active_hours_end: int | None,
    daily_session_rotation: bool,
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

        runtime_seconds = run_launch_command_once(launch_command, heartbeat_driver_argv)

        if not is_within_active_hours(active_hours_start, active_hours_end):
            continue

        if runtime_seconds > STABLE_RUNTIME_THRESHOLD_SECONDS:
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
        help="Agent name used in restart log messages",
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
    return parser.parse_args()


def main() -> None:
    install_exit_signal_handlers()
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
    )


if __name__ == "__main__":
    main()
