# Rename Claude Code sessions for better identification in /resume
{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/rename-session;

  rename-session = pkgs.writeShellScriptBin "rename-session" ''
    export PATH="${pkgs.jq}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ rename-session ];
}
