from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
LAUNCH_INSTRUCTIONS = (
    REPOSITORY_ROOT
    / "agent-harness/harnesses/claude-code/launch/interactive-session-instructions.nix"
)
TOOL_SELECTION_INSTRUCTIONS = (
    REPOSITORY_ROOT
    / "agent-harness/harnesses/claude-code/launch/interactive-tool-usage.md"
)


def test_claude_interactive_prompt_projects_dedicated_tool_selection():
    launch_source = LAUNCH_INSTRUCTIONS.read_text(encoding="utf-8")
    tool_selection = TOOL_SELECTION_INSTRUCTIONS.read_text(encoding="utf-8")

    assert "./interactive-tool-usage.md" in launch_source
    assert "Read, not cat, head, or tail" in tool_selection
    assert "Edit, not Write, changes an existing file" in tool_selection
    assert "Before changing existing code, use Read" in tool_selection
    assert (
        "Do not substitute\nGrep, Glob, or Bash output for those reads"
        in tool_selection
    )
