{ config, ... }:
let
  dotfilesSkillsDir = ../../../agents/skills;

  getSkillNamesFromDir =
    dir:
    if builtins.pathExists dir then
      let
        directoryEntries = builtins.readDir dir;
      in
      builtins.filter (
        name:
        directoryEntries.${name} == "directory"
        && name != ".system"
        && builtins.pathExists (dir + "/${name}/SKILL.md")
      ) (builtins.attrNames directoryEntries)
    else
      [ ];

  skillNames = getSkillNamesFromDir dotfilesSkillsDir;

  coreAgentRawContent = builtins.readFile ../../../agents/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
  coreAgentBodyWithoutFrontmatter = builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4;

  codexSkillLinks = builtins.listToAttrs (
    map (name: {
      name = ".codex/skills/${name}";
      value = {
        source = "${dotfilesSkillsDir}/${name}";
        recursive = true;
      };
    }) skillNames
  );

  coreSkillFromAgentInstructions = {
    ".codex/skills/core/SKILL.md".text = ''
      ---
      name: core
      description: Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.
      ---

      ${coreAgentBodyWithoutFrontmatter}
    '';
  };

  liveAplicacoesAtendimentoTriageSkillLink = {
    ".codex/skills/aplicacoes-atendimento-triage".source =
      config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/repo/aplicacoes-atendimento-triage";
  };
in
{
  home.file =
    codexSkillLinks // coreSkillFromAgentInstructions // liveAplicacoesAtendimentoTriageSkillLink;
}
