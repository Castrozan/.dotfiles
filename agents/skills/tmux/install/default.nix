{ pkgs }:
let
  scriptsDirectory = ../scripts;
in
{
  packages = [
    (pkgs.writeShellScriptBin "claude-show-session" ''
      export PATH="${pkgs.coreutils}/bin:${pkgs.gnused}/bin:${pkgs.jq}/bin:$PATH"
      ${builtins.readFile "${scriptsDirectory}/claude-show-session"}
    '')
  ];
}
