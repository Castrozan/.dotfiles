{ pkgs, lib }:
let
  hooksRootDirectory = ./runtime;
  wellputSource = import ../agent-instructions/wellput-plugin/upstream.nix { inherit pkgs; };

  listHookScriptsRecursively = import ./list-hook-scripts-recursively.nix { inherit lib; };

  allHookScriptsAcrossSubdirectories = builtins.filter (
    entry:
    !(lib.hasPrefix "common/human_facing_reply/" entry.relativePathToHooksRoot)
    && entry.relativePathToHooksRoot != "stop/end_of_turn_format_guard_handler.py"
  ) (listHookScriptsRecursively hooksRootDirectory);

  installModeForHookScript = filename: if lib.hasSuffix ".sh" filename then "0755" else "0644";

  installCommandForHookScript =
    entry:
    "install -m ${installModeForHookScript entry.flatDeploymentFilename} "
    + "${hooksRootDirectory + "/${entry.relativePathToHooksRoot}"} "
    + ''"$out/${entry.flatDeploymentFilename}"'';

  hookPython = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.websockets
  ]);
  hookPythonInterpreter = "${hookPython}/bin/python3";

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
    --replace-fail "@hookPythonInterpreter@" "${hookPythonInterpreter}" \
    --replace-fail "@wellputReplyHook@" "${wellputSource}/hooks/reply_hook.py"
  substituteInPlace "$out/servant_identity_handler.py" \
    --replace-fail "@servantsDomainDirectory@" "${servantsDomainDirectory}"
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$out" ${hookPythonInterpreter} -c \
    'import wellput_hook_handler'
''
