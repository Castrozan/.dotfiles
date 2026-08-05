{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "cursorsh" (builtins.readFile ./cursor/scripts/cursorsh))
  ];
}
