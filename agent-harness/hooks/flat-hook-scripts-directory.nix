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

  hookPython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.markdown-it-py ]);
  hookPythonInterpreter = "${hookPython}/bin/python3";

  # The servant handler imports the servants domain rather than being flattened
  # beside it: `catalog.py` and `roster.py` are names generic enough to collide in
  # a directory this flat, and the domain is not a hooks concern.
  servantsDomainDirectory = ../servants;
in
pkgs.runCommandLocal "agent-hook-scripts" { } ''
  mkdir -p "$out"
  ${lib.concatMapStringsSep "\n" installCommandForHookScript allHookScriptsAcrossSubdirectories}
  install -m 0644 ${../harnesses/codex/scripts/shared_server/codex_client_context.py} "$out/codex_client_context.py"
  patchShebangs "$out/run-hook.sh"
  substituteInPlace "$out/run-hook.sh" \
    --replace-fail "@hookPythonInterpreter@" "${hookPythonInterpreter}"
  substituteInPlace "$out/servant_identity_handler.py" \
    --replace-fail "@servantsDomainDirectory@" "${servantsDomainDirectory}"
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$out" ${hookPythonInterpreter} -c \
    'from reply_rule_catalog import template_violations_in_reply; template_violations_in_reply("")'
''
