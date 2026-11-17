from __future__ import annotations

import os
import re
import subprocess

from shell_simple_commands import words_after_command_wrappers

BETHA_GITLAB_HOST = "gitlab.services.betha.cloud"
GLAB_BUILT_IN_DEFAULT_HOST = "gitlab.com"
GLAB_HOST_VARIABLES = ("GITLAB_HOST", "GL_HOST")
VARIABLE_EXPORTING_COMMAND = "export"
DIRECTORY_CHANGING_COMMAND = "cd"
LOOKUP_TIMEOUT_SECONDS = 5
HOST_IN_A_LOCATION_PATTERN = re.compile(
    r"(?:[a-z][a-z0-9+.-]*://)?(?:[^@/]*@)?(?P<host>[^/:?#]+)", re.IGNORECASE
)


def _lookup_output(lookup_command, working_directory=None):
    try:
        completed = subprocess.run(
            lookup_command,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=LOOKUP_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout if completed.returncode == 0 else ""


def remote_locations_of(working_directory):
    remote_lines = _lookup_output(["git", "remote", "-v"], working_directory)
    return {
        remote_fields[1]
        for remote_fields in map(str.split, remote_lines.splitlines())
        if len(remote_fields) > 1
    }


def ssh_configured_host(written_host):
    for setting in _lookup_output(["ssh", "-G", "--", written_host]).splitlines():
        setting_name, _, setting_value = setting.partition(" ")
        if setting_name == "hostname":
            return setting_value.strip().lower()
    return written_host


def glab_default_host():
    return _lookup_output(["glab", "config", "get", "host"])


def _travels_over_ssh(location):
    if "://" in location:
        return location.lower().startswith("ssh://")
    return ":" in location


def _host_of(location):
    host_match = HOST_IN_A_LOCATION_PATTERN.match(location.strip())
    if host_match is None:
        return ""
    written_host = host_match.group("host").lower()
    if _travels_over_ssh(location):
        return ssh_configured_host(written_host)
    return written_host


def _words_before_the_invocation(simple_command_words):
    invocation_words = words_after_command_wrappers(simple_command_words)
    return simple_command_words[: len(simple_command_words) - len(invocation_words)]


def _sets_variables_for_later_commands(simple_command_words):
    invocation_words = words_after_command_wrappers(simple_command_words)
    return invocation_words[:1] == [VARIABLE_EXPORTING_COMMAND]


def _host_variables_set_in_the_command(simple_commands, creation_position):
    variable_setting_words = [
        word
        for earlier_command_words in simple_commands[:creation_position]
        if _sets_variables_for_later_commands(earlier_command_words)
        for word in earlier_command_words
    ]
    variable_setting_words += _words_before_the_invocation(
        simple_commands[creation_position]
    )
    host_variables = {}
    for word in variable_setting_words:
        variable_name, assignment_separator, assigned_value = word.partition("=")
        if assignment_separator and variable_name in GLAB_HOST_VARIABLES:
            host_variables[variable_name] = assigned_value
    return host_variables


def _host_forced_through_the_environment(simple_commands, creation_position):
    host_variables = {
        **os.environ,
        **_host_variables_set_in_the_command(simple_commands, creation_position),
    }
    for variable_name in GLAB_HOST_VARIABLES:
        forced_host = _host_of(host_variables.get(variable_name, ""))
        if forced_host and forced_host != GLAB_BUILT_IN_DEFAULT_HOST:
            return forced_host
    return ""


def _directory_the_creation_runs_in(
    simple_commands, creation_position, session_directory
):
    working_directory = session_directory
    for earlier_command_words in simple_commands[:creation_position]:
        invocation_words = words_after_command_wrappers(earlier_command_words)
        if invocation_words[:1] != [DIRECTORY_CHANGING_COMMAND]:
            continue
        destination = invocation_words[-1] if invocation_words[1:] else "~"
        working_directory = os.path.join(
            working_directory, os.path.expanduser(destination)
        )
    return working_directory


def _hosts_glab_may_reach(simple_commands, creation_position, session_directory):
    forced_host = _host_forced_through_the_environment(
        simple_commands, creation_position
    )
    if forced_host:
        return {forced_host}
    working_directory = _directory_the_creation_runs_in(
        simple_commands, creation_position, session_directory
    )
    remote_hosts = {
        _host_of(remote_location)
        for remote_location in remote_locations_of(working_directory)
    }
    return remote_hosts or {_host_of(glab_default_host())}


def creation_targets_betha_gitlab(
    creation_form, simple_commands, creation_position, session_directory
):
    arguments = words_after_command_wrappers(simple_commands[creation_position])[1:]
    named_location = creation_form.location_named_by(arguments)
    if named_location:
        return _host_of(named_location) == BETHA_GITLAB_HOST
    return BETHA_GITLAB_HOST in _hosts_glab_may_reach(
        simple_commands, creation_position, session_directory
    )
