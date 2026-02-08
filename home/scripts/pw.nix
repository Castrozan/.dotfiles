{ pkgs, ... }:
let
  pwJs = pkgs.writeText "pw.js" (builtins.readFile ../../agents/skills/browser/pw.js);
  pwScript = builtins.readFile ../../agents/scripts/pw.sh;

  pw = pkgs.writeShellScriptBin "pw" ''
    export PW_JS="${pwJs}"
    ${pwScript}
  '';
in
{
  home.packages = [ pw ];
}
