import pytest

from codex_client_arguments import parse_launch_arguments
from codex_client_configuration import command_line_configuration, thread_configuration


def test_profile_and_command_line_overrides_preserve_nested_workspace_settings(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    (tmp_path / "work.config.toml").write_text(
        'developer_instructions="work"\n[mcp_servers.project]\ncommand="server"\n'
    )
    result = command_line_configuration(
        [
            "--profile=work",
            "-c",
            'mcp_servers.project.env.SELECTED="yes"',
            "resume",
            "--last",
        ]
    )
    assert result["developer_instructions"] == "work"
    assert result["mcp_servers"]["project"] == {
        "command": "server",
        "env": {"SELECTED": "yes"},
    }


@pytest.mark.parametrize(
    "arguments,command",
    [
        (["--model", "exec", "resume", "--last"], "resume"),
        (["-c", "model=custom", "exec", "prompt"], "exec"),
        (["-C", "/project", "fork", "identifier"], "fork"),
        (["--", "--profile=literal-prompt"], "--profile=literal-prompt"),
    ],
)
def test_native_option_values_are_not_mistaken_for_subcommands(arguments, command):
    assert parse_launch_arguments(arguments).command == command


def test_stdio_mcp_environment_uses_the_client_and_preserves_explicit_values():
    configuration = {
        "mcp_servers": {
            "project": {
                "command": "server",
                "env_vars": ["WORKSPACE_TOKEN"],
                "env": {"EXPLICIT": "configured"},
            }
        }
    }
    result = thread_configuration(
        {},
        configuration,
        {
            "PATH": "client-bin",
            "WORKSPACE_TOKEN": "client-token",
            "UNRELATED_SECRET": "hidden",
        },
    )
    assert result["config"]["mcp_servers"]["project"]["env"] == {
        "PATH": "client-bin",
        "WORKSPACE_TOKEN": "client-token",
        "EXPLICIT": "configured",
    }
