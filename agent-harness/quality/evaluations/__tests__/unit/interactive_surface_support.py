import json
import re
import subprocess
from functools import cache
from pathlib import Path

from instructions.instruction_surface_scanner import REPO_ROOT
from instructions.reply_format_instructions import expand_reply_format_instructions

WELLPUT_UPSTREAM_PIN_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "wellput-plugin"
    / "upstream.nix"
)
PINNED_WELLPUT_SOURCE_EXPRESSION = (
    "import @upstream@ { pkgs.fetchFromGitHub = source: builtins.fetchTarball { "
    'url = "https://github.com/${source.owner}/${source.repo}/archive/${source.rev}.tar.gz"; '
    "sha256 = source.hash; }; }"
)
PINNED_WELLPUT_SOURCE_EVALUATION_TIMEOUT_SECONDS = 300

HUMANIZE_SKILL_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "writing"
    / "humanize"
    / "SKILL.md"
)
INTERACTIVE_POLICY_PATH = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "interactive-communication.md"
)
MAXIMUM_ALWAYS_INJECTED_INTERACTIVE_POLICY_BYTES = 5500
MAXIMUM_ON_DEMAND_HUMANIZE_PACKAGE_BYTES = 19000

INTERACTIVE_POLICY_SOURCE = "agent-instructions/interactive-communication.md"
ON_DEMAND_HUMANIZE_SOURCES = ("agent-instructions/skills/writing/humanize/SKILL.md",)
INTERACTIVE_GENERATOR_PATHS = (
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "claude-code"
    / "launch"
    / "interactive-session-instructions.nix",
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "codex"
    / "interactive-instructions.nix",
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "opencode"
    / "instructions"
    / "interactive-instructions.nix",
    REPO_ROOT / "agent-harness" / "harnesses" / "pi" / "interactive-instructions.nix",
)
INTERACTIVE_LAUNCH_SOURCES = (
    REPO_ROOT
    / "agent-harness/harnesses/claude-code/launch/interactive-claude-command.nix",
    REPO_ROOT / "agent-harness" / "harnesses" / "codex" / "scripts" / "codex",
    REPO_ROOT / "agent-harness/harnesses/opencode/scripts/launch_opencode.sh",
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "pi"
    / "scripts"
    / "launch-pi-with-the-interactive-reply-rules.sh",
)


@cache
def pinned_wellput_reply_format_configuration() -> dict:
    pinned_source = subprocess.run(
        [
            "nix",
            "eval",
            "--raw",
            "--impure",
            "--expr",
            PINNED_WELLPUT_SOURCE_EXPRESSION.replace(
                "@upstream@", str(WELLPUT_UPSTREAM_PIN_PATH)
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=PINNED_WELLPUT_SOURCE_EVALUATION_TIMEOUT_SECONDS,
    ).stdout
    return json.loads((Path(pinned_source) / "wellput.json").read_text())


def expanded_interactive_policy() -> str:
    return expand_reply_format_instructions(
        INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8"),
        pinned_wellput_reply_format_configuration(),
    )


def interactive_policy_section(tag: str) -> str:
    policy = expanded_interactive_policy()
    heading = re.compile(
        r"^### " + re.escape(tag.replace("_", " ")) + r"\n",
        re.IGNORECASE | re.MULTILINE,
    )
    section = heading.split(policy, 1)[1].split("\n### ", 1)[0]
    return " ".join(section.split())
