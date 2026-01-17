# Safe Claude Code session termination script
{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/claude-exit;
in
let
  claude-exit = pkgs.writeShellScriptBin "claude-exit" ''
    export PATH="${pkgs.procps}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ claude-exit ];
}
