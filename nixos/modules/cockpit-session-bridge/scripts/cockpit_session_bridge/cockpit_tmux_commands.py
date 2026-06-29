import shlex

NON_INTERACTIVE_SSH_OPTIONS = [
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=accept-new",
    "-o",
    "ConnectTimeout=10",
]
REMOTE_TMUX_EXECUTABLE = "tmux"
SESSION_NAME_LIST_FORMAT = "#{session_name}"
WINDOW_INVENTORY_LIST_FORMAT = (
    "#{session_name}\t#{window_id}\t#{pane_current_command}\t#{window_name}"
)


def build_cockpit_tmux_command(
    tmux_executable_path,
    tmux_socket_name,
    *tmux_arguments,
    remote_ssh_host="",
    allocate_remote_pseudoterminal=False,
):
    tmux_command_executable = (
        REMOTE_TMUX_EXECUTABLE if remote_ssh_host else tmux_executable_path
    )
    if tmux_socket_name:
        local_tmux_command = [
            tmux_command_executable,
            "-L",
            tmux_socket_name,
            *tmux_arguments,
        ]
    else:
        local_tmux_command = [tmux_command_executable, *tmux_arguments]
    if not remote_ssh_host:
        return local_tmux_command
    remote_ssh_invocation = ["ssh", *NON_INTERACTIVE_SSH_OPTIONS]
    if allocate_remote_pseudoterminal:
        remote_ssh_invocation.append("-tt")
    remote_ssh_invocation.append(remote_ssh_host)
    return [*remote_ssh_invocation, shlex.join(local_tmux_command)]


def build_list_sessions_command(
    tmux_executable_path, enumeration_socket_name, *, remote_ssh_host=""
):
    return build_cockpit_tmux_command(
        tmux_executable_path,
        enumeration_socket_name,
        "list-sessions",
        "-F",
        SESSION_NAME_LIST_FORMAT,
        remote_ssh_host=remote_ssh_host,
    )


def build_list_windows_command(
    tmux_executable_path, enumeration_socket_name, *, remote_ssh_host=""
):
    return build_cockpit_tmux_command(
        tmux_executable_path,
        enumeration_socket_name,
        "list-windows",
        "-a",
        "-F",
        WINDOW_INVENTORY_LIST_FORMAT,
        remote_ssh_host=remote_ssh_host,
    )


def build_open_session_command(
    tmux_executable_path, mutation_socket_name, session_name
):
    return build_cockpit_tmux_command(
        tmux_executable_path,
        mutation_socket_name,
        "new-session",
        "-d",
        "-s",
        session_name,
    )


def build_rename_session_command(
    tmux_executable_path, mutation_socket_name, current_session_name, new_session_name
):
    return build_cockpit_tmux_command(
        tmux_executable_path,
        mutation_socket_name,
        "rename-session",
        "-t",
        current_session_name,
        new_session_name,
    )


def build_close_session_command(
    tmux_executable_path, mutation_socket_name, session_name
):
    return build_cockpit_tmux_command(
        tmux_executable_path, mutation_socket_name, "kill-session", "-t", session_name
    )


def build_open_window_command(
    tmux_executable_path,
    mutation_socket_name,
    session_name,
    window_title,
    agent_launch_command,
):
    open_window_command = build_cockpit_tmux_command(
        tmux_executable_path,
        mutation_socket_name,
        "new-window",
        "-t",
        session_name,
        "-n",
        window_title,
    )
    if agent_launch_command:
        open_window_command.append(agent_launch_command)
    return open_window_command


def build_close_window_command(
    tmux_executable_path, mutation_socket_name, window_identifier
):
    return build_cockpit_tmux_command(
        tmux_executable_path,
        mutation_socket_name,
        "kill-window",
        "-t",
        window_identifier,
    )


def build_attach_session_command(
    tmux_executable_path, enumeration_socket_name, attach_target, *, remote_ssh_host=""
):
    return build_cockpit_tmux_command(
        tmux_executable_path,
        enumeration_socket_name,
        "attach-session",
        "-t",
        attach_target,
        remote_ssh_host=remote_ssh_host,
        allocate_remote_pseudoterminal=True,
    )
