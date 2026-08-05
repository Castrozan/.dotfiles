from cockpit_herdr_commands import CockpitHerdrConnection, build_server_status_command
from cockpit_herdr_multiplexer import CockpitHerdrMultiplexer
from cockpit_multiplexer_port import run_multiplexer_subprocess_command
from cockpit_tmux_commands import build_list_sessions_command
from cockpit_tmux_multiplexer import CockpitTmuxMultiplexer

RUNNING_HERDR_SERVER_STATUS_MARKER = "status: running"


async def detect_cockpit_multiplexer(
    settings, socket_policy, *, subprocess_runner=None
):
    subprocess_runner = subprocess_runner or run_multiplexer_subprocess_command
    herdr_status_result = await _probe(
        subprocess_runner,
        build_server_status_command(
            CockpitHerdrConnection(
                herdr_executable_path=settings.cockpit_herdr_executable_path,
                remote_ssh_host=socket_policy.remote_ssh_host,
            )
        ),
    )
    if _reports_a_running_herdr_server(herdr_status_result):
        return build_herdr_multiplexer(settings, socket_policy, subprocess_runner)
    tmux_sessions_result = await _probe(
        subprocess_runner,
        build_list_sessions_command(
            settings.cockpit_tmux_executable_path,
            socket_policy.enumeration_socket_name,
            remote_ssh_host=socket_policy.remote_ssh_host,
        ),
    )
    if tmux_sessions_result is not None and tmux_sessions_result.exit_code == 0:
        return build_tmux_multiplexer(settings, socket_policy, subprocess_runner)
    if herdr_status_result is not None:
        return build_herdr_multiplexer(settings, socket_policy, subprocess_runner)
    return build_tmux_multiplexer(settings, socket_policy, subprocess_runner)


def build_herdr_multiplexer(settings, socket_policy, subprocess_runner):
    return CockpitHerdrMultiplexer(
        settings.cockpit_herdr_executable_path,
        settings.cockpit_herdr_session_name,
        remote_ssh_host=socket_policy.remote_ssh_host,
        subprocess_runner=subprocess_runner,
    )


def build_tmux_multiplexer(settings, socket_policy, subprocess_runner):
    return CockpitTmuxMultiplexer(
        settings.cockpit_tmux_executable_path,
        socket_policy,
        subprocess_runner=subprocess_runner,
    )


def _reports_a_running_herdr_server(herdr_status_result):
    return (
        herdr_status_result is not None
        and herdr_status_result.exit_code == 0
        and RUNNING_HERDR_SERVER_STATUS_MARKER in herdr_status_result.standard_output
    )


async def _probe(subprocess_runner, probe_command):
    try:
        return await subprocess_runner(probe_command)
    except OSError:
        return None
