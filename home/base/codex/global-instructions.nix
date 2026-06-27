_:
let
  coreAgentRawContent = builtins.readFile ../../../agents/core_rules/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
  coreAgentBodyWithoutFrontmatter = builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4;
in
{
  home.file.".codex/AGENTS.md".text = coreAgentBodyWithoutFrontmatter;
}
