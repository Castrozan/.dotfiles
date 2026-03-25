{
  config,
  lib,
  ...
}:
let
  inherit (config.home) homeDirectory;
  skillSetsBaseDirectory = "${homeDirectory}/.local/share/claude-skill-sets";
  personalSkillSetDirectory = "${skillSetsBaseDirectory}/personal";

  externalSkillSets = {
    aplicacoes = {
      description = "Aplicações team operations";
      skillName = "aplicacoes-atendimento-triage";
      sourceRepositoryPath = "${homeDirectory}/repo/aplicacoes-atendimento-triage";
    };
    protocolo = {
      description = "Protocolo Digital operations";
      skillName = "protocolo-atendimento-triage";
      sourceRepositoryPath = "${homeDirectory}/repo/protocolo-atendimento-triage";
    };
    triage = {
      description = "Generic triage operations";
      skillName = "atendimento-triage";
      sourceRepositoryPath = "${homeDirectory}/repo/atendimento-triage";
    };
  };

  generateSkillSetWrapperActivationCommands = lib.concatMapStringsSep "\n" (
    name:
    let
      skillSet = externalSkillSets.${name};
      skillSetDirectory = "${skillSetsBaseDirectory}/${name}";
      skillsDiscoveryDirectory = "${skillSetDirectory}/.claude/skills";
    in
    ''
      if [ -d "${skillSet.sourceRepositoryPath}" ]; then
        mkdir -p "${skillsDiscoveryDirectory}"
        ln -sfn "${skillSet.sourceRepositoryPath}" "${skillsDiscoveryDirectory}/${skillSet.skillName}"
      else
        rm -rf "${skillSetDirectory}"
      fi
    ''
  ) (builtins.attrNames externalSkillSets);

  cleanupOldAplicacoesFromGlobalSkills = ''
    rm -rf "${homeDirectory}/.claude/skills/aplicacoes-atendimento-triage"
  '';

  cleanupOldPluginWrappers = ''
    for dir in "${skillSetsBaseDirectory}"/*/; do
      rm -rf "$dir/.claude-plugin" "$dir/skills"
    done
  '';

  defaultClaudeFishFunction = ''
    function claude --description "Claude Code with personal skills"
      command claude --add-dir ${personalSkillSetDirectory} $argv
    end
  '';

  generateFishFunctionForSkillSet =
    name:
    let
      skillSet = externalSkillSets.${name};
      skillSetDirectory = "${skillSetsBaseDirectory}/${name}";
    in
    ''
      function claude-${name} --description "${skillSet.description}"
        command claude --add-dir ${skillSetDirectory} $argv
      end
    '';

  allFishFunctionsForExternalSkillSets = lib.concatStringsSep "\n" (
    [ defaultClaudeFishFunction ]
    ++ map generateFishFunctionForSkillSet (builtins.attrNames externalSkillSets)
  );
in
{
  xdg.configFile."fish/conf.d/claude-skill-sets.fish".text = allFishFunctionsForExternalSkillSets;

  home.activation.createExternalSkillSetWrappers =
    lib.hm.dag.entryAfter
      [
        "writeBoundary"
      ]
      ''
        ${cleanupOldAplicacoesFromGlobalSkills}
        ${cleanupOldPluginWrappers}
        ${generateSkillSetWrapperActivationCommands}
      '';
}
