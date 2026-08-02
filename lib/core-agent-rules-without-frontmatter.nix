let
  coreAgentRawContent = builtins.readFile ../agents/core_rules/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
in
builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4
