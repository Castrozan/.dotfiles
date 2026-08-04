{
  config,
  hostname,
  lib,
  ...
}:
let
  interactiveAgentSkills = import ../../../agents/interactive-agent-skills.nix { inherit hostname; };

  opencodeInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames { };

  opencodeSkillsPath = "${config.home.homeDirectory}/.config/opencode/skills";

  globalOpencodeSkills = builtins.listToAttrs (
    map (dirname: {
      name = ".config/opencode/skills/${dirname}";
      value = {
        source = interactiveAgentSkills.skillSourceDirectoryByName.${dirname};
        recursive = true;
      };
    }) opencodeInteractiveSkillNames
  );

  coreAgentBodyWithoutFrontmatter = import ../../../lib/core-agent-rules-without-frontmatter.nix;

  coreSkillFromAgentInstructions = {
    ".config/opencode/skills/core/SKILL.md".text = ''
      ---
      name: core
      description: Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.
      ---

      ${coreAgentBodyWithoutFrontmatter}
    '';
  };

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
  home.file = globalOpencodeSkills // coreSkillFromAgentInstructions // allSkillsIndexSkillFile;

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
