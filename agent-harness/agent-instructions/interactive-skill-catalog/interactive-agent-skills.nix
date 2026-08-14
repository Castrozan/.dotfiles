{ hostname }:
let
  skillSetBuilders = import ./skill-set-builders.nix { inherit hostname; };

  inherit (skillSetBuilders)
    allSkillNames
    privateSkillNames
    skillSourceDirectoryByName
    skillDirectorySymlinksAtPrefix
    ;

  defaultInteractiveSkillNames = [
    "architecture"
    "browser"
    "coding"
    "deep-work"
    "deliver"
    "devenv"
    "docs"
    "explore"
    "goal-prompt"
    "herdr"
    "humanize"
    "instructions"
    "orchestrate"
    "research"
    "restart"
    "review"
    "workspace"
  ];

  dotfilesRepoSkillNames = [
    "agent-harness"
    "nix"
  ];

  privateIndexedSkillNamesFile =
    ../../../private-configuration/machines + "/${hostname}/indexed-skill-names.nix";

  privateIndexedSkillNames =
    if builtins.pathExists privateIndexedSkillNamesFile then
      import privateIndexedSkillNamesFile
    else
      [ ];

  uninjectedSkillNames = builtins.filter (
    skillName: !(builtins.elem skillName privateIndexedSkillNames)
  ) privateSkillNames;

  skillNamesOffTheGlobalSurface = dotfilesRepoSkillNames ++ uninjectedSkillNames;

  effectiveInteractiveSkillNames =
    {
      add ? [ ],
      remove ? [ ],
    }:
    builtins.filter (skillName: !(builtins.elem skillName remove)) (
      defaultInteractiveSkillNames ++ add
    );

  reachableSkillNames = builtins.filter (
    skillName: !(builtins.elem skillName skillNamesOffTheGlobalSurface)
  ) allSkillNames;

  indexedSkillNamesFor =
    interactiveSkillNames:
    builtins.filter (skillName: !(builtins.elem skillName interactiveSkillNames)) reachableSkillNames;

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
      builtins.readFile (skillSourceDirectoryByName.${skillName} + "/SKILL.md")
    );

  reachableSkillPathFor = skillName: "~/.local/share/agent-skill-index/${skillName}/SKILL.md";

  renderAllSkillsIndexSkill =
    interactiveSkillNames:
    let
      indexedSkillNames = indexedSkillNamesFor interactiveSkillNames;
      commaSeparatedIndexedSkillNames = builtins.concatStringsSep ", " indexedSkillNames;
      description = "Route requests for these indexed capabilities to all-skills, then load the nested skill it names: ${commaSeparatedIndexedSkillNames}";
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
    skillSourceDirectoryByName
    skillDirectorySymlinksAtPrefix
    defaultInteractiveSkillNames
    dotfilesRepoSkillNames
    uninjectedSkillNames
    reachableSkillNames
    effectiveInteractiveSkillNames
    indexedSkillNamesFor
    readSkillDescription
    reachableSkillPathFor
    renderAllSkillsIndexSkill
    ;
}
