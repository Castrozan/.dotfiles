import argparse
import json
import time

from redeploy_signals import (
    install_exit_signal_handlers,
    install_redeploy_signal_handler,
    redeploy_signal_state,
    register_current_child_process_id,
)
from restart_scheduling import (
    INITIAL_RESTART_DELAY_SECONDS,
    MAXIMUM_RESTART_DELAY_SECONDS,
    is_within_active_hours,
    seconds_until_active_hours_start,
    should_reset_backoff,
    should_rotate_session,
)
from session_watchdog import run_launch_command_once


def build_tmux_target(tmux_session: str | None, agent_name: str) -> str | None:
    if not tmux_session:
        return None
    return f"{tmux_session}:{agent_name}"


def load_agent_launch_config(config_file_path: str) -> dict:
    with open(config_file_path) as config_file:
        return json.load(config_file)


def supervise_agent_forever(agent_name: str, config_file_path: str) -> None:
    restart_delay_seconds = INITIAL_RESTART_DELAY_SECONDS
    last_fresh_start_date: str | None = None

    while True:
        try:
            config = load_agent_launch_config(config_file_path)
        except (OSError, ValueError) as config_error:
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Agent {agent_name} could not read launch config "
                f"{config_file_path}: {config_error}. Retrying shortly.",
                flush=True,
            )
            time.sleep(INITIAL_RESTART_DELAY_SECONDS)
            continue

        launch_command = config["launch_command"]
        heartbeat_driver_argv = config.get("heartbeat_driver_argv")
        active_hours_start = config.get("active_hours_start")
        active_hours_end = config.get("active_hours_end")
        daily_session_rotation = config.get("daily_session_rotation", False)
        tmux_target = build_tmux_target(config.get("tmux_session"), agent_name)

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
            redeploy_signal_state.resume_requested = False

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
        description="Run a clawde agent launch command in a restart loop with "
        "exponential backoff, re-reading the agent's launch config on every restart "
        "so a deployment's warm restart applies config changes without a full respawn",
    )
    parser.add_argument(
        "--agent-name",
        required=True,
        help="Agent name used in restart log messages and as the tmux window name",
    )
    parser.add_argument(
        "--config-file",
        required=True,
        help="Path to the agent's JSON launch config (launch command, heartbeat "
        "driver argv, active hours, rotation, tmux session), re-read on every restart",
    )
    return parser.parse_args()


def main() -> None:
    install_exit_signal_handlers()
    install_redeploy_signal_handler()
    arguments = parse_arguments()
    supervise_agent_forever(arguments.agent_name, arguments.config_file)


if __name__ == "__main__":
    main()
