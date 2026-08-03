{
  config,
  lib,
  ...
}:
let
  skillSetBuilders = import ../../../agents/skill-set-builders.nix;
  interactiveAgentSkills = import ../../../agents/interactive-agent-skills.nix;

  opencodeInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames {
    add = [ "browser" ];
  };

  opencodeSkillsPath = "${config.home.homeDirectory}/.config/opencode/skills";

  globalOpencodeSkills = builtins.listToAttrs (
    map (dirname: {
      name = ".config/opencode/skills/${dirname}";
      value = {
        source = skillSetBuilders.dotfilesSkillsDirectory + "/${dirname}";
        recursive = true;
      };
    }) opencodeInteractiveSkillNames
  );

  allSkillsIndexSkill = interactiveAgentSkills.renderAllSkillsIndexSkill opencodeInteractiveSkillNames;

  allSkillsIndexSkillFile = {
    ".config/opencode/skills/all-skills/SKILL.md".text = ''
      ---
      name: all-skills
      description: ${allSkillsIndexSkill.description}
      ---

      ${allSkillsIndexSkill.body}
    '';
  };
in
{
  home.file = globalOpencodeSkills // allSkillsIndexSkillFile;

  home.activation.removeExternalSymlinksCollidingWithOpencodeSkills =
    lib.hm.dag.entryBefore
      [
        "checkLinkTargets"
      ]
      ''
        if [ -d "${opencodeSkillsPath}" ]; then
          for skillName in ${builtins.concatStringsSep " " opencodeInteractiveSkillNames}; do
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
