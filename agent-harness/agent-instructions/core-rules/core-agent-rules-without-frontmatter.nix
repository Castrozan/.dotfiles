let
  coreAgentRawContent = builtins.readFile ./core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
in
builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4
