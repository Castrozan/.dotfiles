import json
import tomllib


from session_server_configuration import server_configuration_for


def configuration_values(arguments):
    return [
        tomllib.loads(argument)[argument.partition("=")[0].strip().strip('"')]
        for argument in arguments[1::2]
    ]


def test_runtime_profile_reaches_the_server_before_cli_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    instructions = 'Servant policy\nKeep the user\'s "title".'
    (tmp_path / "interactive.config.toml").write_text(
        f"developer_instructions = {json.dumps(instructions)}\n"
        'model_reasoning_effort = "high"\n'
    )
    configuration = server_configuration_for(
        ["--profile", "interactive", "-c", 'model_reasoning_effort="max"']
    )
    assert configuration_values(configuration.arguments) == [
        instructions,
        "high",
        "max",
    ]
    assert "--profile" not in configuration.arguments


def test_profile_tables_and_arrays_keep_their_toml_types(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    (tmp_path / "workspace.config.toml").write_text(
        '[features]\nhooks = true\n[mcp_servers."server.with.dots"]\n'
        'command = "a command"\nargs = ["one", "two \\"quoted\\""]\n'
    )
    configuration = server_configuration_for(["-pworkspace"])
    values = configuration_values(configuration.arguments)
    assert values == [
        {"hooks": True},
        {"server.with.dots": {"command": "a command", "args": ["one", 'two "quoted"']}},
    ]


def test_caller_directory_and_feature_overrides_reach_the_private_server(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path.parent)
    configuration = server_configuration_for(
        [
            "-C",
            str(tmp_path),
            "--enable",
            "hooks",
            "--disable",
            "multi_agent",
            "resume",
            "--last",
        ]
    )
    assert configuration.working_directory == tmp_path.resolve()
    assert configuration.arguments == ("--enable", "hooks", "--disable", "multi_agent")


def test_strict_configuration_validation_is_preserved():
    assert server_configuration_for(["--strict-config"]).arguments == (
        "--strict-config",
    )
