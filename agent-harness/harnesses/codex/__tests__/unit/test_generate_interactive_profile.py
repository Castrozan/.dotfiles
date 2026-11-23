import tomllib

from generate_interactive_profile import generate_interactive_profile


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
