{ pkgs, lib, ... }:
# Deploys every hook script flat under ~/.claude/hooks as a SINGLE atomic
# directory symlink, not one symlink per file. Per-file deployment relinks each
# entry independently during home-manager activation, so a hook firing mid-rebuild
# can find its entrypoint while a sibling helper module symlink is briefly gone,
# raising ModuleNotFoundError (the transient SessionStart/PreToolUse hook errors).
# A single directory symlink swaps in one operation: a hook that fires during the
# swap simply does not find its script and run-hook.sh exits 0/1 quietly instead
# of tracebacking. The directory is read-only in the store, so run-hook.sh routes
# Python bytecode to a writable PYTHONPYCACHEPREFIX cache.
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
