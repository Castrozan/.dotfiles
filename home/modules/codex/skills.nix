{ lib, config, ... }:
let
  skillsDir = ../../../agents/skills;
  entries = builtins.readDir skillsDir;
  skillNames = builtins.attrNames (
    lib.filterAttrs (n: t: t == "directory" && n != ".system") entries
  );

  skillLinks = builtins.listToAttrs (
    map (name: {
      name = ".codex/skills/${name}";
      value = {
        source = "${skillsDir}/${name}";
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
  home.file = skillLinks // liveAplicacoesAtendimentoTriageSkillLink;
}
