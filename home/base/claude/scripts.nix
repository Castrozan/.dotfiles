{ pkgs, lib, ... }:
let
  claudeUpdateVersionScript = pkgs.writeShellScriptBin "claude-update-version" ''
    export PATH="${pkgs.nix}/bin:${pkgs.git}/bin:$PATH"
    exec ${pkgs.python312}/bin/python3 ${./scripts/claude-update-version} "$@"
  '';
  memoryWriteScript = pkgs.writeShellScriptBin "memory-write" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/memory-write} "$@"
  '';
  memoryPruneScript = pkgs.writeShellScriptBin "memory-prune" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/memory-prune} "$@"
  '';
  claudeA2aPeerScript = pkgs.writeShellScriptBin "claude-a2a-peer" ''
    export PATH="${pkgs.tmux}/bin:$PATH"
    export PYTHONPATH=${../../../agents}
    exec ${pkgs.python312}/bin/python3 ${./scripts/claude-a2a-peer} "$@"
  '';
  notifyClaudeTurnEndedWithFocusActionScript = pkgs.writeShellScriptBin "notify-claude-turn-ended-with-focus-action" ''
    export PATH="${pkgs.hyprland}/bin:${pkgs.libnotify}/bin:${pkgs.jq}/bin:${pkgs.procps}/bin:${pkgs.coreutils}/bin:$PATH"
    exec ${pkgs.bash}/bin/bash ${./scripts/notify-claude-turn-ended-with-focus-action} "$@"
  '';
in
{
  home.packages = [
    claudeUpdateVersionScript
    memoryWriteScript
    memoryPruneScript
    claudeA2aPeerScript
  ]
  ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
    notifyClaudeTurnEndedWithFocusActionScript
  ];
}
