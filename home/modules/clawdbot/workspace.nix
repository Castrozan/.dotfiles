# OpenClaw workspace symlinks — identity files, rules, skills, subagents
{ lib, ... }:
let
  # Layer 1: Nix-managed workspace files (read-only symlinks)
  clawdbotDir = ../../../agents/clawdbot;
  clawdbotFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir clawdbotDir)
  );
  workspaceSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/${filename}";
      value = {
        source = clawdbotDir + "/${filename}";
      };
    }) clawdbotFiles
  );

  # Files that OpenClaw reads as "Project Context" from workspace root
  nixManagedRootFiles = {
    "SOUL.md" = "soul.md";
    "IDENTITY.md" = "identity.md";
    "USER.md" = "user.md";
    "AGENTS.md" = "agents.md";
  };
  rootSymlinks = lib.mapAttrs' (rootName: srcName: {
    name = "clawd/${rootName}";
    value = {
      source = clawdbotDir + "/${srcName}";
    };
  }) nixManagedRootFiles;

  # Shared rules (from agents/rules/*.md)
  rulesDir = ../../../agents/rules;
  rulesFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir rulesDir)
  );
  rulesSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/rules/${filename}";
      value = {
        source = rulesDir + "/${filename}";
      };
    }) rulesFiles
  );

  # Shared skills (from agents/skills/*/SKILL.md)
  skillsDir = ../../../agents/skills;
  skillDirs = builtins.filter (name: (builtins.readDir skillsDir).${name} == "directory") (
    builtins.attrNames (builtins.readDir skillsDir)
  );
  skillsSymlinks = builtins.listToAttrs (
    map (dirname: {
      name = "clawd/.nix/skills/${dirname}/SKILL.md";
      value = {
        source = skillsDir + "/${dirname}/SKILL.md";
      };
    }) skillDirs
  );

  # Shared subagents (from agents/subagent/*.md)
  subagentDir = ../../../agents/subagent;
  subagentFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir subagentDir)
  );
  subagentSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/subagents/${filename}";
      value = {
        source = subagentDir + "/${filename}";
      };
    }) subagentFiles
  );

  # Agent grid (grid.md as Project Context + shared scripts)
  gridSymlinks = {
    "clawd/GRID.md" = { source = clawdbotDir + "/grid.md"; };
  };

  scriptsDir = ../../../agents/scripts;
  scriptFiles = builtins.filter (name: lib.hasSuffix ".sh" name) (
    builtins.attrNames (builtins.readDir scriptsDir)
  );
  scriptsSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/scripts/${filename}";
      value = {
        source = scriptsDir + "/${filename}";
      };
    }) scriptFiles
  );
in
{
  home.file = workspaceSymlinks // rootSymlinks // rulesSymlinks // skillsSymlinks // subagentSymlinks // gridSymlinks // scriptsSymlinks;
}
