{ lib, ... }:
let
  # Private config from git submodule (private-config/claude)
  # Use path type (not string) for pathExists to avoid premature store path creation
  privateConfigDir = ../../../private-config/claude;
  agentsDir = privateConfigDir + "/agents";
  skillsDir = privateConfigDir + "/skills";

  # Check existence using path type (avoids store path evaluation)
  agentsDirExists = builtins.pathExists agentsDir;
  skillsDirExists = builtins.pathExists skillsDir;

  # Get agent files (filter out .gitkeep)
  privateAgentFiles =
    if agentsDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name && name != ".gitkeep") (
        builtins.attrNames (builtins.readDir agentsDir)
      )
    else
      [ ];

  # Get skill directories (each must have SKILL.md)
  privateSkillDirs =
    if skillsDirExists then
      builtins.filter (
        name: name != ".gitkeep" && builtins.pathExists (skillsDir + "/${name}/SKILL.md")
      ) (builtins.attrNames (builtins.readDir skillsDir))
    else
      [ ];

  # Create home.file entries for private agents
  privateAgentSymlinks = builtins.listToAttrs (
    map (filename: {
      name = ".claude/agents/${filename}";
      value = {
        source = "${agentsDir}/${filename}";
      };
    }) privateAgentFiles
  );

  # Create home.file entries for private skills
  privateSkillSymlinks = builtins.listToAttrs (
    map (dirname: {
      name = ".claude/skills/${dirname}";
      value = {
        source = "${skillsDir}/${dirname}";
        recursive = true;
      };
    }) privateSkillDirs
  );
in
{
  home.file = lib.mkIf (agentsDirExists || skillsDirExists) (
    privateAgentSymlinks // privateSkillSymlinks
  );
}
