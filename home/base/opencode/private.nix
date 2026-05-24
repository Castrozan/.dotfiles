{ lib, ... }:
let
  inherit (import ./lib.nix) colorNameToHex processAgentFile;

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

  privateAgentEntries = builtins.listToAttrs (
    map (filename: {
      name = ".config/opencode/agents/${filename}";
      value = {
        text = processAgentFile colorNameToHex (builtins.readFile (agentsDir + "/${filename}"));
      };
    }) privateAgentFiles
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
  home.file = lib.mkIf (agentsDirExists || skillsDirExists) (
    privateAgentEntries // privateSkillEntries
  );
}
