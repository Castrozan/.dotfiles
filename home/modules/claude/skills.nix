{ config, lib, ... }:
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
    }) skillNames
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

  openclawWorkspacePaths = map (
    agentName: "${config.home.homeDirectory}/${config.openclaw.agents.${agentName}.workspace}/skills"
  ) (lib.attrNames config.openclaw.enabledAgents);

  allSkillTargetDirectories = [
    "${config.home.homeDirectory}/.claude/skills"
    "${config.home.homeDirectory}/.codex/skills"
  ]
  ++ openclawWorkspacePaths;

  copyCommands = lib.concatMapStringsSep "\n" (targetDir: ''
    rm -rf "${targetDir}/aplicacoes-atendimento-triage"
    cp -r "${sourceRepoPath}" "${targetDir}/aplicacoes-atendimento-triage"
  '') allSkillTargetDirectories;
in
{
  home.file = globalClaudeSkills // coreSkillFromAgentInstructions;

  home.activation.copyAplicacoesAtendimentoTriageSkill = lib.hm.dag.entryAfter [
    "writeBoundary"
  ] copyCommands;
}
