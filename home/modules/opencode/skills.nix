{
  config,
  lib,
  ...
}:
let
  dotfilesSkillsDir = ../../../agents/skills;

  getSkillNamesFromDir =
    dir:
    if builtins.pathExists dir then
      builtins.filter (name: builtins.pathExists (dir + "/${name}/SKILL.md")) (
        builtins.attrNames (builtins.readDir dir)
      )
    else
      [ ];

  skillNames = getSkillNamesFromDir dotfilesSkillsDir;

  opencodeSkillsPath = "${config.home.homeDirectory}/.config/opencode/skills";

  globalOpencodeSkills = builtins.listToAttrs (
    map (dirname: {
      name = ".config/opencode/skills/${dirname}";
      value = {
        source = dotfilesSkillsDir + "/${dirname}";
        recursive = true;
      };
    }) skillNames
  );
in
{
  home.file = globalOpencodeSkills;

  home.activation.removeExternalSymlinksCollidingWithOpencodeSkills =
    lib.hm.dag.entryBefore
      [
        "checkLinkTargets"
      ]
      ''
        if [ -d "${opencodeSkillsPath}" ]; then
          for skillName in ${builtins.concatStringsSep " " skillNames}; do
            skillPath="${opencodeSkillsPath}/$skillName"
            if [ -L "$skillPath" ]; then
              linkTarget=$(readlink "$skillPath")
              if [ "''${linkTarget#${config.home.homeDirectory}/.nix-profile}" = "$linkTarget" ] && \
                 [ "''${linkTarget#/nix/store}" = "$linkTarget" ]; then
                rm "$skillPath"
              fi
            fi
          done
        fi
      '';
}
