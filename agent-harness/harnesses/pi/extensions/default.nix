{ pkgs, lib }:
let
  scripts = import ../../../hooks/flat-hook-scripts-directory.nix { inherit pkgs lib; };
  piHookDispatcher = pkgs.writeShellScript "pi-human-facing-reply-hook-dispatcher" ''
    exec ${scripts}/run-hook.sh ${scripts}/stop-dispatcher.py --surface=pi
  '';
  piSessionStartDispatcher = pkgs.writeShellScript "pi-wellput-session-start" ''
    exec ${scripts}/run-hook.sh ${scripts}/session-start-dispatcher.py --surface=pi
  '';
in
pkgs.replaceVars ./human-facing-reply-guard.js {
  inherit piHookDispatcher piSessionStartDispatcher;
}
