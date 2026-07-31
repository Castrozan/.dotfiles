{
  pkgs,
  derivationName,
  claudeAgentDefinitionsDirectory,
}:
pkgs.runCommand derivationName
  {
    nativeBuildInputs = [ pkgs.python312 ];
    CLAUDE_SUBAGENT_DEFINITIONS_DIRECTORY = claudeAgentDefinitionsDirectory;
  }
  ''
    export OPENCODE_AGENT_DEFINITIONS_DIRECTORY="$out"
    python3 ${./scripts/translate_claude_subagents_to_opencode_agents.py}
  ''
