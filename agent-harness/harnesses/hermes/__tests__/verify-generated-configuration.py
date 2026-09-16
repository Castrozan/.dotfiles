import argparse
from pathlib import Path

import yaml

from instructions.ai_instruction_format import inspect_markdown_instruction


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("configuration", type=Path)
    parser.add_argument("hook_command")
    arguments = parser.parse_args()
    configuration = yaml.safe_load(arguments.configuration.read_text())
    assert configuration["hooks_auto_accept"] is True
    assert configuration["security"]["allow_lazy_installs"] is False
    assert configuration["plugins"]["enabled"] == ["herdr-agent-state"]
    assert configuration["hooks"]["pre_tool_call"] == [
        {"command": arguments.hook_command, "timeout": 10}
    ]
    assert configuration["hooks"]["post_tool_call"] == [
        {"command": arguments.hook_command, "timeout": 20}
    ]
    assert configuration["model"] == {"provider": "openai-codex", "model": "gpt-5.5"}
    assert configuration["agent"]["reasoning_effort"] == "xhigh"
    assert configuration["toolsets"] == ["hermes-cli"]
    instructions = configuration["agent"]["system_prompt"]
    assert not inspect_markdown_instruction(instructions).violations
    assert "### Interactive session\n" in instructions
    assert "(SOUL.md#evidence)" in instructions
    assert "(skills/humanize/SKILL.md#representation-selection)" in instructions


if __name__ == "__main__":
    main()
