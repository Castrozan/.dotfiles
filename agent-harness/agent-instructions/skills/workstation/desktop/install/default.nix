{ pkgs }:
if pkgs.stdenv.isDarwin then
  import ./computer-use-mcp-package.nix { inherit pkgs; }
else
  import ./hypruse-package.nix { inherit pkgs; }
