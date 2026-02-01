{ lib, ... }:
let
  agentDir = ../../../agents/openclaw;

  rootFiles = {
    "SOUL.md" = "soul.md";
    "IDENTITY.md" = "identity.md";
    "USER.md" = "user.md";
    "AGENTS.md" = "agents.md";
    "AI-TOOLS.md" = "ai-tools.md";
    "INSTRUCTIONS.md" = "instructions.md";
    "TOOLS-BASE.md" = "tools-base.md";
    "TODO.md" = "TODO.md";
    "GRID.md" = "grid.md";
  };

  contextFiles = lib.mapAttrs' (rootName: srcName: {
    name = "clawd/${rootName}";
    value = {
      text = builtins.readFile (agentDir + "/${srcName}");
    };
  }) rootFiles;
in
{
  home.file = contextFiles;
}
