{ pkgs, lib, ... }:
let
  privateConfigDir = ../../../private-configuration/claude;
  agentsDir = privateConfigDir + "/agents";
  skillsDir = privateConfigDir + "/skills";

  agentsDirExists = builtins.pathExists agentsDir;
  skillsDirExists = builtins.pathExists skillsDir;

  privateAgentDefinitions =
    if agentsDirExists then
      import ./translate-claude-agent-definitions.nix {
        inherit pkgs;
        derivationName = "opencode-private-agent-definitions";
        claudeAgentDefinitionsDirectory = agentsDir;
      }
    else
      null;

  privateAgentFileNames =
    if agentsDirExists then
      builtins.filter (fileName: lib.hasSuffix ".md" fileName) (
        builtins.attrNames (builtins.readDir agentsDir)
      )
    else
      [ ];

  privateSkillDirs =
    if skillsDirExists then
      builtins.filter (
        name: name != ".gitkeep" && builtins.pathExists (skillsDir + "/${name}/SKILL.md")
      ) (builtins.attrNames (builtins.readDir skillsDir))
    else
      [ ];

  privateAgentEntries = builtins.listToAttrs (
    map (fileName: {
      name = ".config/opencode/agent/${fileName}";
      value = {
        source = "${privateAgentDefinitions}/${fileName}";
      };
    }) privateAgentFileNames
  );

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
