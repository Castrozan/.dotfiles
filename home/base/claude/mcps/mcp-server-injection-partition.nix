{
  lib,
  allMcpServerNames,
}:
let
  agentOnlyMcpServerNames = [ "a2a" ];

  hostGatedBrowserMcpServerNames = [ "vivaldi-devtools" ];

  retiredMcpServerNames = [
    "browser-use"
    "figma"
    "figma-read"
  ];

  interactivelyInjectedMcpServerNames = lib.subtractLists agentOnlyMcpServerNames allMcpServerNames;

  managedMcpServerNames = lib.unique (
    allMcpServerNames ++ hostGatedBrowserMcpServerNames ++ retiredMcpServerNames
  );
in
{
  inherit
    agentOnlyMcpServerNames
    hostGatedBrowserMcpServerNames
    retiredMcpServerNames
    interactivelyInjectedMcpServerNames
    managedMcpServerNames
    ;
}
