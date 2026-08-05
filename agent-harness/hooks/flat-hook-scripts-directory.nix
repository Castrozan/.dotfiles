{ pkgs, lib }:
let
  hooksRootDirectory = ./runtime;

  listHookScriptsRecursively = import ./list-hook-scripts-recursively.nix { inherit lib; };

  allHookScriptsAcrossSubdirectories = listHookScriptsRecursively hooksRootDirectory;

  installModeForHookScript = filename: if lib.hasSuffix ".sh" filename then "0755" else "0644";

  installCommandForHookScript =
    entry:
    "install -m ${installModeForHookScript entry.flatDeploymentFilename} "
    + "${hooksRootDirectory + "/${entry.relativePathToHooksRoot}"} "
    + ''"$out/${entry.flatDeploymentFilename}"'';

  hookPythonInterpreter = "${pkgs.python312}/bin/python3";
in
pkgs.runCommandLocal "agent-hook-scripts" { } ''
  mkdir -p "$out"
  ${lib.concatMapStringsSep "\n" installCommandForHookScript allHookScriptsAcrossSubdirectories}
  substituteInPlace "$out/run-hook.sh" \
    --replace-fail "@hookPythonInterpreter@" "${hookPythonInterpreter}"
''
