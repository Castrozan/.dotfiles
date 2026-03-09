{ lib, config, ... }:
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

  codexSkillLinks = builtins.listToAttrs (
    map (name: {
      name = ".codex/skills/${name}";
      value = {
        source = "${dotfilesSkillsDir}/${name}";
        recursive = true;
      };
    }) skillNames
  );

  liveAplicacoesAtendimentoTriageSkillLink = {
    ".codex/skills/aplicacoes-atendimento-triage".source =
      config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/repo/aplicacoes-atendimento-triage";
  };
in
{
  home.file = codexSkillLinks // liveAplicacoesAtendimentoTriageSkillLink;
}
