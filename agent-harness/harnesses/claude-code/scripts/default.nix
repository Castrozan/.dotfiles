{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
  claudeUpdateVersionScript = pkgs.writeShellScriptBin "claude-update-version" ''
    export PATH="${pkgs.nix}/bin:${pkgs.git}/bin:$PATH"
    exec ${pkgs.python312}/bin/python3 ${./claude-update-version} "$@"
  '';
  launchCommandDetachedIntoNewSessionScript = pkgs.writeShellScriptBin "launch-command-detached-into-new-session" ''
    exec ${pkgs.python312}/bin/python3 ${./launch-command-detached-into-new-session} "$@"
  '';
  claudeA2aPeerScript = pkgs.writeShellScriptBin "claude-a2a-peer" ''
    export PATH="${herdrPackage}/bin:$PATH"
    export PYTHONPATH=${../../../../agent-harness/agent-to-agent-communication/server}
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
    launchCommandDetachedIntoNewSessionScript
    claudeA2aPeerScript
  ]
  ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
    notifyClaudeTurnEndedWithFocusActionScript
  ];
}
