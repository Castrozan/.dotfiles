{ pkgs, lib, ... }:
let
  claudeUpdateVersionScript = pkgs.writeShellScriptBin "claude-update-version" ''
    export PATH="${pkgs.nix}/bin:${pkgs.git}/bin:$PATH"
    exec ${pkgs.python312}/bin/python3 ${./claude-update-version} "$@"
  '';
  memoryWriteScript = pkgs.writeShellScriptBin "memory-write" ''
    exec ${pkgs.python312}/bin/python3 ${./memory-write} "$@"
  '';
  memoryPruneScript = pkgs.writeShellScriptBin "memory-prune" ''
    exec ${pkgs.python312}/bin/python3 ${./memory-prune} "$@"
  '';
  launchCommandDetachedIntoNewSessionScript = pkgs.writeShellScriptBin "launch-command-detached-into-new-session" ''
    exec ${pkgs.python312}/bin/python3 ${./launch-command-detached-into-new-session} "$@"
  '';
  claudeA2aPeerScript = pkgs.writeShellScriptBin "claude-a2a-peer" ''
    export PATH="${pkgs.tmux}/bin:$PATH"
    export PYTHONPATH=${../../../../agents}
    exec ${pkgs.python312}/bin/python3 ${./claude-a2a-peer} "$@"
  '';
  notifyClaudeTurnEndedWithFocusActionScript = pkgs.writeShellScriptBin "notify-claude-turn-ended-with-focus-action" ''
    export PATH="${pkgs.hyprland}/bin:${pkgs.libnotify}/bin:${pkgs.jq}/bin:${pkgs.procps}/bin:${pkgs.coreutils}/bin:$PATH"
    exec ${pkgs.bash}/bin/bash ${./notify-claude-turn-ended-with-focus-action} "$@"
  '';
in
{
  home.packages = [
    claudeUpdateVersionScript
    memoryWriteScript
    memoryPruneScript
    launchCommandDetachedIntoNewSessionScript
    claudeA2aPeerScript
  ]
  ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
    notifyClaudeTurnEndedWithFocusActionScript
  ];
}
