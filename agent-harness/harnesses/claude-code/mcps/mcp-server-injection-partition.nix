{
  lib,
  allMcpServerNames,
}:
let
  agentOnlyMcpServerNames = [ ];

  hostGatedRemoteMemoryMcpServerNames = [ "mem0" ];

  retiredMcpServerNames = [
    "a2a"
    "brave-devtools"
    "browser-use"
    "figma"
    "figma-read"
    "vivaldi-devtools"
  ];

  interactivelyInjectedMcpServerNames = lib.subtractLists agentOnlyMcpServerNames allMcpServerNames;

  managedMcpServerNames = lib.unique (
    allMcpServerNames ++ hostGatedRemoteMemoryMcpServerNames ++ retiredMcpServerNames
  );
in
{
  inherit
    agentOnlyMcpServerNames
    hostGatedRemoteMemoryMcpServerNames
    retiredMcpServerNames
    interactivelyInjectedMcpServerNames
    managedMcpServerNames
    ;
}
