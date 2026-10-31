import argparse
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("configuration", type=Path)
    parser.add_argument("hook_command")
    arguments = parser.parse_args()
    configuration = yaml.safe_load(arguments.configuration.read_text())
    assert configuration["hooks_auto_accept"] is True
    assert configuration["security"]["allow_lazy_installs"] is False
    assert configuration["plugins"]["enabled"] == ["herdr-agent-state", "dotfiles"]
    assert configuration["hooks"]["pre_tool_call"] == [
        {"command": arguments.hook_command, "timeout": 10}
    ]
    assert configuration["hooks"]["post_tool_call"] == [
        {"command": arguments.hook_command, "timeout": 20}
    ]
    assert configuration["model"] == {
        "provider": "openai-codex",
        "model": "gpt-6.1-sol",
    }
    assert configuration["agent"] == {"reasoning_effort": "xhigh"}
    assert configuration["auth"] == {"adopt_external_logins": False}
    assert configuration["approvals"] == {"mode": "off"}
    assert configuration["toolsets"] == ["hermes-cli"]


if __name__ == "__main__":
    main()
