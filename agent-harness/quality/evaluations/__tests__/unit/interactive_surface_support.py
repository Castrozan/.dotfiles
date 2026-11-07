import re

from instructions.instruction_surface_scanner import REPO_ROOT
from instructions.reply_format_instructions import expand_reply_format_instructions


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


def interactive_policy_section(tag: str) -> str:
    policy = expand_reply_format_instructions(
        INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8")
    )
    heading = re.compile(
        r"^### " + re.escape(tag.replace("_", " ")) + r"\n",
        re.IGNORECASE | re.MULTILINE,
    )
    section = heading.split(policy, 1)[1].split("\n### ", 1)[0]
    return " ".join(section.split())
