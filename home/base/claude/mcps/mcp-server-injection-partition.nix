{
  lib,
  allMcpServerNames,
}:
let
  agentOnlyMcpServerNames = [ "a2a" ];

  hostGatedBrowserMcpServerNames = [ "vivaldi-devtools" ];

  hostGatedRemoteMemoryMcpServerNames = [ "mem0" ];

  retiredMcpServerNames = [
    "brave-devtools"
    "browser-use"
    "figma"
    "figma-read"
  ];

  interactivelyInjectedMcpServerNames = lib.subtractLists agentOnlyMcpServerNames allMcpServerNames;

  managedMcpServerNames = lib.unique (
    allMcpServerNames
    ++ hostGatedBrowserMcpServerNames
    ++ hostGatedRemoteMemoryMcpServerNames
    ++ retiredMcpServerNames
  );
in
{
  inherit
    agentOnlyMcpServerNames
    hostGatedBrowserMcpServerNames
    hostGatedRemoteMemoryMcpServerNames
    retiredMcpServerNames
    interactivelyInjectedMcpServerNames
    managedMcpServerNames
    ;
}
