{
  lib,
  mkEvalCheck,
  cfg,
  hasFilePrefix,
}:
let
  interactiveAgentSkills = import ../../../../agents/interactive-agent-skills.nix {
    hostname = "test";
  };

  claudeInteractiveSkillNames = interactiveAgentSkills.effectiveInteractiveSkillNames { };

  uninjectedSkillsStayOutOfEverySurface = builtins.all (
    skillName:
    !(builtins.hasAttr ".claude/skills/${skillName}" cfg.home.file)
    && !(builtins.hasAttr ".local/share/agent-skill-index/${skillName}" cfg.home.file)
    && !(builtins.elem skillName (
      interactiveAgentSkills.indexedSkillNamesFor claudeInteractiveSkillNames
    ))
  ) interactiveAgentSkills.uninjectedSkillNames;

  generatedMachineTierSkillNames = [
    "all-skills"
    "core"
  ];

  sortedAlphabetically = builtins.sort builtins.lessThan;

  machineTierSkillNames = lib.unique (
    map (fileName: builtins.head (lib.splitString "/" (lib.removePrefix ".claude/skills/" fileName))) (
      builtins.filter (fileName: lib.hasPrefix ".claude/skills/" fileName) (
        builtins.attrNames cfg.home.file
      )
    )
  );

  machineTierCarriesOnlyTheCuratedSet =
    sortedAlphabetically machineTierSkillNames
    == sortedAlphabetically (claudeInteractiveSkillNames ++ generatedMachineTierSkillNames);

  privateMachinesDirectory = ../../../../private-config/machines;

  privateMachineNames =
    if builtins.pathExists privateMachinesDirectory then
      builtins.attrNames (builtins.readDir privateMachinesDirectory)
    else
      [ ];

  privateMachineSkillNamesFor =
    machineName:
    let
      privateMachineSkillsDirectory = privateMachinesDirectory + "/${machineName}/skills";
    in
    if builtins.pathExists privateMachineSkillsDirectory then
      builtins.filter (
        skillName: builtins.pathExists (privateMachineSkillsDirectory + "/${skillName}/SKILL.md")
      ) (builtins.attrNames (builtins.readDir privateMachineSkillsDirectory))
    else
      [ ];

  everyPrivateMachineSkillIsCatalogued = builtins.all (
    machineName:
    let
      cataloguedSkillNames =
        (import ../../../../agents/interactive-agent-skills.nix { hostname = machineName; }).allSkillNames;
    in
    builtins.all (skillName: builtins.elem skillName cataloguedSkillNames) (
      privateMachineSkillNamesFor machineName
    )
  ) privateMachineNames;
in
{
  claude-skills-directory =
    mkEvalCheck "claude-skills-directory" (hasFilePrefix ".claude/skills/")
      "skills directory entries should be in home.file";

  claude-machine-tier-carries-the-curated-interactive-set =
    mkEvalCheck "claude-machine-tier-carries-the-curated-interactive-set"
      (builtins.all (
        skillName: builtins.hasAttr ".claude/skills/${skillName}" cfg.home.file
      ) claudeInteractiveSkillNames)
      "every curated interactive skill must deploy into the machine tier at .claude/skills; a dropped skill silently vanishes from every interactive session";

  claude-machine-tier-carries-nothing-beyond-the-curated-set =
    mkEvalCheck "claude-machine-tier-carries-nothing-beyond-the-curated-set"
      machineTierCarriesOnlyTheCuratedSet
      "the machine tier at .claude/skills must hold exactly the curated set plus the generated core and all-skills entries; a second module injecting its own skills there bypasses the curated list and silently reinflates every session's system prompt";

  claude-machine-tier-carries-the-generated-all-skills-index =
    mkEvalCheck "claude-machine-tier-carries-the-generated-all-skills-index"
      (builtins.hasAttr ".claude/skills/all-skills/SKILL.md" cfg.home.file)
      "the generated all-skills index must deploy into the machine tier; it is the only reachability path for every non-curated skill, and a session without it cannot reach them";

  claude-indexed-skills-stay-reachable-outside-the-machine-tier =
    mkEvalCheck "claude-indexed-skills-stay-reachable-outside-the-machine-tier"
      (builtins.all (
        skillName: builtins.hasAttr ".local/share/agent-skill-index/${skillName}" cfg.home.file
      ) (interactiveAgentSkills.indexedSkillNamesFor claudeInteractiveSkillNames))
      "every skill excluded from the curated machine tier must stay reachable at .local/share/agent-skill-index, because the all-skills index points there; a skill that is neither curated nor mirrored is stranded on disk";

  claude-uninjected-skills-reach-no-global-surface =
    mkEvalCheck "claude-uninjected-skills-reach-no-global-surface" uninjectedSkillsStayOutOfEverySurface
      "a skill named in uninjectedSkillNames must stay out of the machine tier, out of the all-skills index and out of the reachability mirror; it exists for the one agent that declares it by path, and any of those three surfaces would put it back in every session's budget";

  claude-private-machine-skills-are-catalogued =
    mkEvalCheck "claude-private-machine-skills-are-catalogued" everyPrivateMachineSkillIsCatalogued
      "every private-config/machines/<hostname>/skills skill must be enumerated by the shared catalog for that hostname; a private root the catalog never reads is either injected behind the curated list's back or missing from the all-skills index entirely";
}
