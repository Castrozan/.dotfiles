from instruction_surface_scanner import REPO_ROOT


HUMANIZE_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "skills" / "humanize"
)
HUMANIZE_SKILL_PATH = HUMANIZE_DIRECTORY / "SKILL.md"
INTERACTIVE_POLICY_PATH = HUMANIZE_DIRECTORY / "interactive-communication.md"
MAXIMUM_ALWAYS_INJECTED_INTERACTIVE_POLICY_BYTES = 5000
MAXIMUM_ON_DEMAND_HUMANIZE_PACKAGE_BYTES = 19000

INTERACTIVE_POLICY_SOURCE = (
    "agent-instructions/skills/humanize/interactive-communication.md"
)
ON_DEMAND_HUMANIZE_SOURCES = ("agent-instructions/skills/humanize/SKILL.md",)
INTERACTIVE_LAUNCHER_PATHS = (
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "claude-code"
    / "skill-injection"
    / "interactive-sessions.nix",
    REPO_ROOT / "agent-harness" / "harnesses" / "codex" / "package.nix",
    REPO_ROOT / "agent-harness" / "harnesses" / "opencode" / "opencode.nix",
    REPO_ROOT / "agent-harness" / "harnesses" / "pi" / "package.nix",
)
INTERACTIVE_LAUNCH_SOURCES = (
    *INTERACTIVE_LAUNCHER_PATHS[:3],
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "pi"
    / "scripts"
    / "launch-pi-with-the-interactive-reply-rules.sh",
)


def interactive_policy_section(tag: str) -> str:
    policy = INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8")
    section = policy.split(f"<{tag}>", 1)[1].split(f"</{tag}>", 1)[0]
    return " ".join(section.split())
