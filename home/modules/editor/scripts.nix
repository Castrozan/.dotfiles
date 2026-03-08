{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "cursorsh" (builtins.readFile ./scripts/cursorsh))
  ];
}
