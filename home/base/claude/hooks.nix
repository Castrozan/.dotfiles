{ pkgs, lib, ... }:
let
  hooksDir = ../../../agents/hooks;

  listHookScriptsRecursively = import ./list-hook-scripts-recursively.nix { inherit lib; };

  allHookScriptsAcrossSubdirectories = listHookScriptsRecursively hooksDir;

  installModeForHookScript = filename: if lib.hasSuffix ".sh" filename then "0755" else "0644";

  installCommandForHookScript =
    entry:
    "install -m ${installModeForHookScript entry.flatDeploymentFilename} "
    + "${hooksDir + "/${entry.relativePathToHooksRoot}"} "
    + ''"$out/${entry.flatDeploymentFilename}"'';

  flatlyDeployedHooksDirectory = pkgs.runCommandLocal "claude-code-hooks" { } ''
    mkdir -p "$out"
    ${lib.concatMapStringsSep "\n" installCommandForHookScript allHookScriptsAcrossSubdirectories}
  '';
in
{
  home.file.".claude/hooks".source = flatlyDeployedHooksDirectory;
}
