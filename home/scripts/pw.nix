{ pkgs, ... }:
let
  pwDaemonJs = pkgs.writeText "pw-daemon.js" (
    builtins.readFile ../../agents/skills/browser/scripts/pw-daemon.js
  );
  pwScript = builtins.readFile ../../agents/skills/browser/scripts/pw.sh;

  pw = pkgs.writeShellScriptBin "pw" ''
    export PW_DAEMON_JS="${pwDaemonJs}"
    ${pwScript}
  '';
in
{
  home.packages = [ pw ];
}
