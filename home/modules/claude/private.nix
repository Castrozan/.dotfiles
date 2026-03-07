{ lib, ... }:
let
  privateConfigDir = ../../../private-config/claude;
  agentsDir = privateConfigDir + "/agents";
  skillsDir = privateConfigDir + "/skills";

  agentsDirExists = builtins.pathExists agentsDir;
  skillsDirExists = builtins.pathExists skillsDir;

  privateAgentFiles =
    if agentsDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name && name != ".gitkeep") (
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

  privateAgentSymlinks = builtins.listToAttrs (
    map (filename: {
      name = ".claude/agents/${filename}";
      value = {
        source = "${agentsDir}/${filename}";
      };
    }) privateAgentFiles
  );

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
