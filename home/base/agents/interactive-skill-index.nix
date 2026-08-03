{
  lib,
  ...
}:
let
  skillSetBuilders = import ../../../agents/skill-set-builders.nix;

  reachableSkillDirectorySymlinks = builtins.listToAttrs (
    map (skillName: {
      name = ".local/share/agent-skill-index/${skillName}";
      value = {
        source = skillSetBuilders.dotfilesSkillsDirectory + "/${skillName}";
      };
    }) skillSetBuilders.allSkillNames
  );
in
{
  home.file = reachableSkillDirectorySymlinks;
}
