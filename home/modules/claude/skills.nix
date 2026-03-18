{
  config,
  lib,
  pkgs,
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

  globalClaudeSkills = builtins.listToAttrs (
    map (dirname: {
      name = ".claude/skills/${dirname}";
      value = {
        source = dotfilesSkillsDir + "/${dirname}";
        recursive = true;
      };
    }) skillNamesWithoutPlatformExclusions
  );

  coreAgentRawContent = builtins.readFile ../../../agents/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
  coreAgentBodyWithoutFrontmatter = builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4;

  coreSkillFromAgentInstructions = {
    ".claude/skills/core/SKILL.md".text = ''
      ---
      name: core
      description: Display core agent behavior instructions. Use when user wants to see, review, or reference the core rules, or when injecting core instructions as context into subagents, oneshot sessions, or external tools.
      ---

      ${coreAgentBodyWithoutFrontmatter}
    '';
  };

  sourceRepoPath = "${config.home.homeDirectory}/repo/aplicacoes-atendimento-triage";

  openclawModuleIsAvailable = builtins.hasAttr "openclaw" config;

  skillsThatRequireOpenclawInfrastructure = [
    "openclaw"
    "grid"
    "assistant-cron"
    "hey-clever"
  ];

  skillNamesWithoutPlatformExclusions =
    if openclawModuleIsAvailable then
      skillNames
    else
      builtins.filter (name: !builtins.elem name skillsThatRequireOpenclawInfrastructure) skillNames;

  openclawWorkspacePaths =
    if openclawModuleIsAvailable then
      map (
        agentName: "${config.home.homeDirectory}/${config.openclaw.agents.${agentName}.workspace}/skills"
      ) (lib.attrNames config.openclaw.enabledAgents)
    else
      [ ];

  allSkillTargetDirectories = [
    "${config.home.homeDirectory}/.claude/skills"
    "${config.home.homeDirectory}/.codex/skills"
  ]
  ++ openclawWorkspacePaths;

  copyCommands =
    let
      getSourceRevisionCommand = "${pkgs.git}/bin/git -C \"${sourceRepoPath}\" rev-parse HEAD 2>/dev/null || true";
      getInstalledRevisionCommand =
        targetDir: "cat \"${targetDir}/aplicacoes-atendimento-triage/.git-rev\" 2>/dev/null || true";
    in
    lib.concatMapStringsSep "\n" (targetDir: ''
      if [ -d "${sourceRepoPath}" ]; then
        SOURCE_REV=$(${getSourceRevisionCommand})
        INSTALLED_REV=$(${getInstalledRevisionCommand targetDir})
        if [ "$SOURCE_REV" != "$INSTALLED_REV" ]; then
          rm -rf "${targetDir}/aplicacoes-atendimento-triage"
          cp -r "${sourceRepoPath}" "${targetDir}/aplicacoes-atendimento-triage"
          echo "$SOURCE_REV" > "${targetDir}/aplicacoes-atendimento-triage/.git-rev"
        fi
      else
        rm -rf "${targetDir}/aplicacoes-atendimento-triage"
      fi
    '') allSkillTargetDirectories;
in
{
  home.file = globalClaudeSkills // coreSkillFromAgentInstructions;

  home.activation.copyAplicacoesAtendimentoTriageSkill = lib.hm.dag.entryAfter [
    "writeBoundary"
  ] copyCommands;
}
