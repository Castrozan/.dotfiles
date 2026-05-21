{ lib, ... }:
let
  hooksDir = ../../../agents/hooks;

  listHookScriptsRecursively = import ./list-hook-scripts-recursively.nix { inherit lib; };

  allHookScriptsAcrossSubdirectories = listHookScriptsRecursively hooksDir;

  createFlatSymlinksForHookScripts =
    hookScriptEntries:
    builtins.listToAttrs (
      map (entry: {
        name = ".claude/hooks/${entry.flatDeploymentFilename}";
        value = {
          source = hooksDir + "/${entry.relativePathToHooksRoot}";
          executable = lib.hasSuffix ".sh" entry.flatDeploymentFilename;
        };
      }) hookScriptEntries
    );

  preventDirectoryOptimization = {
    ".claude/hooks/.hm-keep".text = "";
  };
in
{
  home.file =
    createFlatSymlinksForHookScripts allHookScriptsAcrossSubdirectories // preventDirectoryOptimization;
}
