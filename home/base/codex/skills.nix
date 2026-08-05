{
  config,
  hostname,
  lib,
  pkgs,
  ...
}:
let
  interactiveAgentSkills =
    import
      ../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
      { inherit hostname; };

  codexInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames { };

  codexSkillsPath = "${config.home.homeDirectory}/.codex/skills";

  coreAgentBodyWithoutFrontmatter = import ../../../lib/core-agent-rules-without-frontmatter.nix;

  codexSkillLinks = interactiveAgentSkills.skillDirectorySymlinksAtPrefix ".codex/skills" codexInteractiveSkillNames;

  coreSkillDirectory = pkgs.writeTextDir "SKILL.md" ''
    ---
    name: core
    description: Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.
    ---

    ${coreAgentBodyWithoutFrontmatter}
  '';

  coreSkillFromAgentInstructions = {
    ".codex/skills/core".source = coreSkillDirectory;
  };

  allSkillsIndexSkill = interactiveAgentSkills.renderAllSkillsIndexSkill codexInteractiveSkillNames;

  allSkillsIndexSkillDirectory = pkgs.writeTextDir "SKILL.md" ''
    ---
    name: all-skills
    description: ${allSkillsIndexSkill.description}
    ---

    ${allSkillsIndexSkill.body}
  '';

  allSkillsIndexSkillFile = {
    ".codex/skills/all-skills".source = allSkillsIndexSkillDirectory;
  };

in
{
  home.file = codexSkillLinks // coreSkillFromAgentInstructions // allSkillsIndexSkillFile;

  home.activation.removeLegacyCodexSkillDirectories = lib.hm.dag.entryBefore [ "checkLinkTargets" ] ''
    CODEX_SKILLS_PATH="${codexSkillsPath}" \
    COREUTILS_BIN="${pkgs.coreutils}/bin" \
    GREP_BIN="${pkgs.gnugrep}/bin/grep" \
    ${pkgs.bash}/bin/bash ${./scripts/replace-legacy-codex-skill-directories}
  '';
}
