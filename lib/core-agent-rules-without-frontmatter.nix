let
  coreAgentRawContent = builtins.readFile ../agent-harness/agent-instructions/core-rules/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
in
builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4
