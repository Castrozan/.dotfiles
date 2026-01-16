{ lib, config, ... }:
let
  # Private config directory outside the dotfiles repo
  privateConfigDir = "${config.home.homeDirectory}/.private-config/claude";
  privateAgentsDir = "${privateConfigDir}/agents";
  privateSkillsDir = "${privateConfigDir}/skills";

  # Check if private config directories exist
  privateAgentsDirExists = builtins.pathExists privateAgentsDir;
  privateSkillsDirExists = builtins.pathExists privateSkillsDir;

  # Get agent files if directory exists
  privateAgentFiles =
    if privateAgentsDirExists then
      builtins.filter
        (name: lib.hasSuffix ".md" name)
        (builtins.attrNames (builtins.readDir privateAgentsDir))
    else
      [ ];

  # Get skill directories if directory exists (each must have SKILL.md)
  privateSkillDirs =
    if privateSkillsDirExists then
      builtins.filter
        (name: builtins.pathExists "${privateSkillsDir}/${name}/SKILL.md")
        (builtins.attrNames (builtins.readDir privateSkillsDir))
    else
      [ ];

  # Create home.file entries for private agents
  privateAgentSymlinks = builtins.listToAttrs (map
    (filename: {
      name = ".claude/agents/${filename}";
      value = { source = "${privateAgentsDir}/${filename}"; };
    })
    privateAgentFiles);

  # Create home.file entries for private skills
  privateSkillSymlinks = builtins.listToAttrs (map
    (dirname: {
      name = ".claude/skills/${dirname}";
      value = {
        source = "${privateSkillsDir}/${dirname}";
        recursive = true;
      };
    })
    privateSkillDirs);
in
{
  # Only create symlinks if private configs exist
  home.file = lib.mkIf (privateAgentsDirExists || privateSkillsDirExists)
    (privateAgentSymlinks // privateSkillSymlinks);
}
