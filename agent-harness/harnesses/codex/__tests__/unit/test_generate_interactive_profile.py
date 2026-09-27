import tomllib

from generate_interactive_profile import generate_interactive_profile


def test_preserves_instruction_bytes_without_replacing_builtin_instructions():
    instructions = 'First line\n"""quotes"""\n$HOME `command` \\ path\n'

    configuration = tomllib.loads(
        generate_interactive_profile(instructions, {}).decode()
    )

    assert configuration == {"developer_instructions": instructions}


def test_preserves_workspace_override_types_and_nested_keys():
    configuration = tomllib.loads(
        generate_interactive_profile(
            "instructions",
            {
                "model_reasoning_effort": '"high"',
                "features.hooks": "true",
                "agents.max_threads": "2",
                "model": "unquoted-model-name",
                "shell_environment_policy.include_only": '["PATH", "HOME"]',
            },
        ).decode()
    )

    assert configuration == {
        "developer_instructions": "instructions",
        "model_reasoning_effort": "high",
        "features": {"hooks": True},
        "agents": {"max_threads": 2},
        "model": "unquoted-model-name",
        "shell_environment_policy": {"include_only": ["PATH", "HOME"]},
    }


def test_explicit_workspace_instructions_keep_their_previous_precedence():
    configuration = tomllib.loads(
        generate_interactive_profile(
            "interactive instructions",
            {"developer_instructions": '"workspace instructions"'},
        ).decode()
    )

    assert configuration["developer_instructions"] == "workspace instructions"
