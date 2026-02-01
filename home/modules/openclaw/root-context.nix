{ lib, ... }:
let
  openclawAgentDir = ../../../agents/openclaw;

  rootContextMappings = {
    "SOUL.md" = "soul.md";
    "IDENTITY.md" = "identity.md";
    "USER.md" = "user.md";
    "AGENTS.md" = "agents.md";
    "AI-TOOLS.md" = "ai-tools.md";
  };

  rootContextSymlinks = lib.mapAttrs' (rootName: srcName: {
    name = "clawd/${rootName}";
    value = {
      source = openclawAgentDir + "/${srcName}";
    };
  }) rootContextMappings;
in
{
  home.file = rootContextSymlinks;
}
