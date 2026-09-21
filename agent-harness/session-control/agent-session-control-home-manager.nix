{
  pkgs,
  inputs,
  ...
}:
let
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
  herdrClientPackage =
    (import ../../machine-configuration/terminal/workspace-manager/herdr/herdr-client-package.nix {
      inherit pkgs herdrPackage;
    }).package;
  agentSessionRestartPreflight = pkgs.writeShellApplication {
    name = "agent-session-restart-preflight";
    runtimeInputs = [ pkgs.python3 ];
    text = ''
      exec python3 ${./agent-session-restart-preflight.py}
    '';
  };
  launchCommandDetachedIntoNewSession = pkgs.writeShellApplication {
    name = "launch-command-detached-into-new-session";
    runtimeInputs = [ pkgs.python3 ];
    text = ''
      exec python3 ${../harnesses/claude-code/scripts/launch-command-detached-into-new-session} "$@"
    '';
  };
  agentSessionCompactWhenIdle = pkgs.writeShellApplication {
    name = "agent-session-compact-when-idle";
    runtimeInputs = [ herdrClientPackage ];
    text = builtins.readFile ./agent-session-compact-when-idle;
  };
in
{
  home.packages = [
    (pkgs.writeShellApplication {
      name = "agent-session";
      runtimeInputs = [
        launchCommandDetachedIntoNewSession
        agentSessionCompactWhenIdle
        agentSessionRestartPreflight
        herdrClientPackage
      ];
      text = builtins.readFile ./agent-session;
    })
  ];
}
