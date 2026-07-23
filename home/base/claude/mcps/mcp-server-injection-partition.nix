{
  lib,
  allMcpServerNames,
}:
let
  agentOnlyMcpServerNames = [ "a2a" ];

  hostGatedRemoteMemoryMcpServerNames = [ "mem0" ];

  retiredMcpServerNames = [
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
