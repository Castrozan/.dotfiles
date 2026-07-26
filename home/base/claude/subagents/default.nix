{ lib, ... }:
let
  subagentDefinitionsDirectory = ../../../../agents/subagents;

  subagentDefinitionFileNames =
    if builtins.pathExists subagentDefinitionsDirectory then
      builtins.filter (fileName: lib.hasSuffix ".md" fileName) (
        builtins.attrNames (builtins.readDir subagentDefinitionsDirectory)
      )
    else
      [ ];

  subagentDefinitionSymlinks = builtins.listToAttrs (
    map (fileName: {
      name = ".claude/agents/${fileName}";
      value.source = subagentDefinitionsDirectory + "/${fileName}";
    }) subagentDefinitionFileNames
  );
in
{
  home.file = subagentDefinitionSymlinks;
}
