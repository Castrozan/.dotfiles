import os
import signal
import subprocess
import sys
import time

AGENT_WRAPPER_PROCESS_MATCH_PATTERN = "agent-wrapper/wrapper.py --agent-name"
GRACE_DELAY_SECONDS_BEFORE_SIGNALING = 2
REDEPLOY_LOG_RELATIVE_PATH = "Library/Logs/clawde-redeploy.log"


def find_agent_wrapper_process_ids() -> list[int]:
    completed_process = subprocess.run(
        ["pgrep", "-f", AGENT_WRAPPER_PROCESS_MATCH_PATTERN],
        capture_output=True,
        text=True,
    )
    return [
        int(line) for line in completed_process.stdout.split() if line.strip().isdigit()
    ]


def signal_agent_wrappers_to_restart_on_continued_sessions(
    agent_wrapper_process_ids: list[int],
) -> None:
    for agent_wrapper_process_id in agent_wrapper_process_ids:
        try:
            os.kill(agent_wrapper_process_id, signal.SIGUSR1)
        except ProcessLookupError:
            pass


def redirect_standard_streams_to_redeploy_log_file() -> None:
    redeploy_log_file_path = os.path.join(
        os.path.expanduser("~"), REDEPLOY_LOG_RELATIVE_PATH
    )
    os.makedirs(os.path.dirname(redeploy_log_file_path), exist_ok=True)
    read_only_devnull_descriptor = os.open(os.devnull, os.O_RDONLY)
    append_log_descriptor = os.open(
        redeploy_log_file_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644
    )
    os.dup2(read_only_devnull_descriptor, sys.stdin.fileno())
    os.dup2(append_log_descriptor, sys.stdout.fileno())
    os.dup2(append_log_descriptor, sys.stderr.fileno())


def detach_into_background_daemon_escaping_caller_process_tree() -> None:
    if os.fork() > 0:
        os._exit(0)
    os.setsid()
    if os.fork() > 0:
        os._exit(0)
    os.chdir("/")
    redirect_standard_streams_to_redeploy_log_file()


def main() -> None:
    agent_wrapper_process_ids = find_agent_wrapper_process_ids()
    if not agent_wrapper_process_ids:
        print("No running clawde agent wrappers matched; nothing to redeploy.")
        return
    print(
        f"Signaling {len(agent_wrapper_process_ids)} clawde agent wrapper(s) to restart "
        "on their continued sessions (claude --continue), detached after a short grace delay."
    )
    sys.stdout.flush()
    detach_into_background_daemon_escaping_caller_process_tree()
    time.sleep(GRACE_DELAY_SECONDS_BEFORE_SIGNALING)
    surviving_agent_wrapper_process_ids = find_agent_wrapper_process_ids()
    print(
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] clawde-redeploy signaling "
        f"{len(surviving_agent_wrapper_process_ids)} wrapper(s) with SIGUSR1"
    )
    signal_agent_wrappers_to_restart_on_continued_sessions(
        surviving_agent_wrapper_process_ids
    )


if __name__ == "__main__":
    main()
