{
  lib,
  allMcpServerNames,
}:
let
  agentOnlyMcpServerNames = [ ];

  retiredMcpServerNames = [
    "a2a"
    "brave-devtools"
    "browser-use"
    "figma"
    "figma-read"
    "mem0"
    "vivaldi-devtools"
  ];

  interactivelyInjectedMcpServerNames = lib.subtractLists agentOnlyMcpServerNames allMcpServerNames;

  managedMcpServerNames = lib.unique (allMcpServerNames ++ retiredMcpServerNames);
in
{
  inherit
    agentOnlyMcpServerNames
    retiredMcpServerNames
    interactivelyInjectedMcpServerNames
    managedMcpServerNames
    ;
}
