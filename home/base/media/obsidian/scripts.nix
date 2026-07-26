{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "obsidian-quick-note" (builtins.readFile ./scripts/obsidian-quick-note))
  ];
}
