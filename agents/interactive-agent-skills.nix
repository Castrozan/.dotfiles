let
  skillSetBuilders = import ./skill-set-builders.nix;

  inherit (skillSetBuilders) allSkillNames;

  defaultInteractiveSkillNames = [
    "agent-harness"
    "architecture"
    "browser"
    "clawde"
    "coding"
    "deep-work"
    "deliver"
    "desktop"
    "docs"
    "exit"
    "explore"
    "herdr"
    "humanize"
    "instructions"
    "nix"
    "research"
    "restart"
    "review"
    "workspace"
  ];

  effectiveInteractiveSkillNames =
    {
      add ? [ ],
      remove ? [ ],
    }:
    builtins.filter (skillName: !(builtins.elem skillName remove)) (
      defaultInteractiveSkillNames ++ add
    );

  indexedSkillNamesFor =
    interactiveSkillNames:
    builtins.filter (skillName: !(builtins.elem skillName interactiveSkillNames)) allSkillNames;

  frontmatterDescriptionFrom =
    skillMarkdownContent:
    let
      startsWithFrontmatterDelimiter = builtins.substring 0 4 skillMarkdownContent == "---\n";
      frontmatterBlock =
        if startsWithFrontmatterDelimiter then
          builtins.elemAt (builtins.split "---\n" skillMarkdownContent) 2
        else
          "";
      splitOnDescriptionMarker = builtins.split "description: " frontmatterBlock;
    in
    if builtins.length splitOnDescriptionMarker >= 3 then
      builtins.elemAt (builtins.split "\n" (builtins.elemAt splitOnDescriptionMarker 2)) 0
    else
      "";

  readSkillDescription =
    skillName:
    frontmatterDescriptionFrom (
      builtins.readFile (skillSetBuilders.dotfilesSkillsDirectory + "/${skillName}/SKILL.md")
    );

  reachableSkillPathFor = skillName: "~/.local/share/agent-skill-index/${skillName}/SKILL.md";

  renderAllSkillsIndexSkill =
    interactiveSkillNames:
    let
      indexedSkillNames = indexedSkillNamesFor interactiveSkillNames;
      commaSeparatedIndexedSkillNames = builtins.concatStringsSep ", " indexedSkillNames;
      description = "This skill compiles all skills not curatedly injected into interactive agent sessions for agent reachability and context management. The skills here are for: ${commaSeparatedIndexedSkillNames}";
      renderedIndexedSkillEntries = builtins.concatStringsSep "\n\n" (
        map (
          skillName:
          "## ${skillName}\n\n${readSkillDescription skillName}\n\nRead the full skill instructions and its knowledge.md at:\n${reachableSkillPathFor skillName}"
        ) indexedSkillNames
      );
    in
    {
      inherit
        description
        indexedSkillNames
        ;
      body = "This index points at every skill not injected into this interactive session. To use one, read its SKILL.md and knowledge.md at the listed path, then follow its instructions.\n\n${renderedIndexedSkillEntries}";
    };
in
{
  inherit
    allSkillNames
    defaultInteractiveSkillNames
    effectiveInteractiveSkillNames
    indexedSkillNamesFor
    readSkillDescription
    reachableSkillPathFor
    renderAllSkillsIndexSkill
    ;
}
