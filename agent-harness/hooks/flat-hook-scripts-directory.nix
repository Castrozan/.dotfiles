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

  # The servant handler imports the servants domain rather than being flattened
  # beside it: `catalog.py` and `roster.py` are names generic enough to collide in
  # a directory this flat, and the domain is not a hooks concern.
  servantsDomainDirectory = ../servants;
in
pkgs.runCommandLocal "agent-hook-scripts" { } ''
  mkdir -p "$out"
  ${lib.concatMapStringsSep "\n" installCommandForHookScript allHookScriptsAcrossSubdirectories}
  patchShebangs "$out/run-hook.sh"
  substituteInPlace "$out/run-hook.sh" \
    --replace-fail "@hookPythonInterpreter@" "${hookPythonInterpreter}"
  substituteInPlace "$out/servant_identity_handler.py" \
    --replace-fail "@servantsDomainDirectory@" "${servantsDomainDirectory}"
''
