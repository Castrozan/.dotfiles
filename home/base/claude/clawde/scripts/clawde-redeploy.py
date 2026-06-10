import json
import os
import re
import signal
import subprocess
import sys
import time

AGENT_WRAPPER_PROCESS_MATCH_PATTERN = "agent-wrapper/wrapper.py --agent-name"
GRACE_DELAY_SECONDS_BEFORE_SIGNALING = 2
REDEPLOY_LOG_RELATIVE_PATH = "Library/Logs/clawde-redeploy.log"
RESUME_NUDGE_SCRIPT_ENVIRONMENT_VARIABLE = "CLAWDE_RESUME_NUDGE_SCRIPT"
AGENT_NAME_PATTERN = re.compile(r"--agent-name (\S+)")
CONFIG_FILE_PATTERN = re.compile(r"--config-file (\S+)")


def find_agent_wrapper_process_ids() -> list[int]:
    completed_process = subprocess.run(
        ["pgrep", "-f", AGENT_WRAPPER_PROCESS_MATCH_PATTERN],
        capture_output=True,
        text=True,
    )
    return [
        int(line) for line in completed_process.stdout.split() if line.strip().isdigit()
    ]


def read_full_command_line(process_id: int) -> str:
    completed_process = subprocess.run(
        ["ps", "-ww", "-p", str(process_id), "-o", "command="],
        capture_output=True,
        text=True,
    )
    return completed_process.stdout.strip()


def read_tmux_session_from_launch_config(config_file_path: str) -> str | None:
    try:
        with open(config_file_path) as config_file:
            return json.load(config_file).get("tmux_session")
    except (OSError, ValueError):
        return None


def describe_agent_wrappers() -> list[dict]:
    agent_wrappers = []
    for process_id in find_agent_wrapper_process_ids():
        command_line = read_full_command_line(process_id)
        agent_name_match = AGENT_NAME_PATTERN.search(command_line)
        config_file_match = CONFIG_FILE_PATTERN.search(command_line)
        if not agent_name_match or not config_file_match:
            continue
        tmux_session = read_tmux_session_from_launch_config(config_file_match.group(1))
        if tmux_session is None:
            continue
        agent_wrappers.append(
            {
                "process_id": process_id,
                "agent_name": agent_name_match.group(1),
                "tmux_session": tmux_session,
            }
        )
    return agent_wrappers


def signal_agent_wrappers_to_restart_on_continued_sessions(
    agent_wrappers: list[dict],
) -> None:
    for agent_wrapper in agent_wrappers:
        try:
            os.kill(agent_wrapper["process_id"], signal.SIGUSR1)
        except ProcessLookupError:
            pass


def spawn_resume_nudges(agent_wrappers: list[dict]) -> None:
    resume_nudge_script_path = os.environ.get(RESUME_NUDGE_SCRIPT_ENVIRONMENT_VARIABLE)
    if not resume_nudge_script_path:
        return
    for agent_wrapper in agent_wrappers:
        subprocess.Popen(
            [
                sys.executable,
                resume_nudge_script_path,
                "--session",
                agent_wrapper["tmux_session"],
                "--window",
                agent_wrapper["agent_name"],
            ]
        )


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
    agent_wrappers = describe_agent_wrappers()
    if not agent_wrappers:
        print("No running clawde agent wrappers matched; nothing to redeploy.")
        return
    print(
        f"Signaling {len(agent_wrappers)} clawde agent wrapper(s) to restart on their "
        "continued sessions (claude --continue) and resume their work, detached after "
        "a short grace delay."
    )
    sys.stdout.flush()
    detach_into_background_daemon_escaping_caller_process_tree()
    time.sleep(GRACE_DELAY_SECONDS_BEFORE_SIGNALING)
    surviving_agent_wrappers = describe_agent_wrappers()
    print(
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] clawde-redeploy signaling "
        f"{len(surviving_agent_wrappers)} wrapper(s) with SIGUSR1 and scheduling "
        "resume nudges"
    )
    signal_agent_wrappers_to_restart_on_continued_sessions(surviving_agent_wrappers)
    spawn_resume_nudges(surviving_agent_wrappers)


if __name__ == "__main__":
    main()
