{ pkgs, lib, ... }:
let
  privateConfigDir = ../../../private-configuration/claude;
  agentsDir = privateConfigDir + "/agents";
  skillsDir = privateConfigDir + "/skills";

  agentsDirExists = builtins.pathExists agentsDir;
  skillsDirExists = builtins.pathExists skillsDir;

  privateSkillDirs =
    if skillsDirExists then
      builtins.filter (
        name: name != ".gitkeep" && builtins.pathExists (skillsDir + "/${name}/SKILL.md")
      ) (builtins.attrNames (builtins.readDir skillsDir))
    else
      [ ];

  privateAgentEntries = lib.optionalAttrs agentsDirExists {
    ".config/opencode/agents" = {
      source = import ./translate-claude-agent-definitions.nix {
        inherit pkgs;
        derivationName = "opencode-private-agent-definitions";
        claudeAgentDefinitionsDirectory = agentsDir;
      };
      recursive = true;
    };
  };

  privateSkillEntries = builtins.listToAttrs (
    map (dirname: {
      name = ".config/opencode/skills/${dirname}";
      value = {
        source = "${skillsDir}/${dirname}";
        recursive = true;
      };
    }) privateSkillDirs
  );
in
{
  home.file = privateAgentEntries // privateSkillEntries;
}
