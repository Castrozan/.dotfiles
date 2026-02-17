{ pkgs, ... }:
let
  browserSkill = import ../../agents/skills/browser/default.nix { inherit pkgs; };

  pwDaemonJs = pkgs.writeText "pw-daemon.js" (
    builtins.readFile ../../agents/skills/browser/scripts/pw-daemon.js
  );
  pwScript = builtins.readFile ../../agents/skills/browser/scripts/pw.sh;

  pw = pkgs.writeShellScriptBin "pw" ''
    export PW_DAEMON_JS="${pwDaemonJs}"
    export PW_NODE_MODULES="${browserSkill.playwrightNodeModules}/node_modules"
    export PATH="${pkgs.nodejs_22}/bin:$PATH"
    ${pwScript}
  '';
in
{
  home.packages = [ pw ];
}
