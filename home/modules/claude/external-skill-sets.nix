{
  config,
  lib,
  pkgs,
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

  find = "${pkgs.findutils}/bin/find";
  mktemp = "${pkgs.coreutils}/bin/mktemp";
  mkdir = "${pkgs.coreutils}/bin/mkdir";
  ln = "${pkgs.coreutils}/bin/ln";
  dirname = "${pkgs.coreutils}/bin/dirname";
  basename = "${pkgs.coreutils}/bin/basename";
  realpath = "${pkgs.coreutils}/bin/realpath";
  rm = "${pkgs.coreutils}/bin/rm";

  workspaceFishFunction = ''
    function claude-workspace --description "Claude Code with workspace skills"
      set -l extend false
      set -l remaining_args

      for arg in $argv
        switch $arg
          case --extend
            set extend true
          case '*'
            set -a remaining_args $arg
        end
      end

      set -l skill_files (${find} . -name "SKILL.md" -type f 2>/dev/null)

      if test (count $skill_files) -eq 0
        echo "No SKILL.md files found in current directory tree"
        return 1
      end

      set -l tmpdir (${mktemp} -d -t claude-workspace.XXXXXX)
      set -l skills_dir "$tmpdir/.claude/skills"
      ${mkdir} -p "$skills_dir"

      for skill_file in $skill_files
        set -l skill_dir (${dirname} "$skill_file")
        set -l skill_name (${basename} "$skill_dir")
        ${ln} -sfn (${realpath} "$skill_dir") "$skills_dir/$skill_name"
      end

      echo "Loaded "(count $skill_files)" workspace skill(s):"
      for skill_file in $skill_files
        set -l skill_name (${basename} (${dirname} "$skill_file"))
        echo "  - $skill_name"
      end

      set -l cmd_args --add-dir $tmpdir

      if test "$extend" = true
        set -a cmd_args --add-dir ${personalSkillSetDirectory}
      end

      command claude $cmd_args $remaining_args
      set -l exit_code $status

      ${rm} -rf "$tmpdir"
      return $exit_code
    end
  '';

  allFishFunctionsForExternalSkillSets = lib.concatStringsSep "\n" (
    [
      defaultClaudeFishFunction
      workspaceFishFunction
    ]
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
