{ lib, config, ... }:
let
  cfg = config.openclaw;
  agentDir = ../../../agents/openclaw;

  rootFiles = {
    "SOUL.md" = "soul.md";
    "IDENTITY.md" = "identity.md";
    "USER.md" = "user.md";
    "AGENTS.md" = "agents.md";
    "AI-TOOLS.md" = "ai-tools.md";
    "TODO.md" = "TODO.md";
    "GRID.md" = "grid.md";
  };

  contextFiles = lib.mapAttrs' (rootName: srcName: {
    name = "${cfg.workspace}/${rootName}";
    value.text = builtins.readFile (agentDir + "/${srcName}");
  }) rootFiles;
in
{
  options.openclaw.workspace = lib.mkOption {
    type = lib.types.str;
    default = "openclaw";
    description = "Workspace directory name relative to home";
  };

  config.home.file = contextFiles;
}
