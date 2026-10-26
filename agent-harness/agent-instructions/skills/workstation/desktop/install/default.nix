{ pkgs }:
{
  packages = [
    (import (
      if pkgs.stdenv.hostPlatform.isDarwin then ./computer-use-mcp-package.nix else ./hypruse-package.nix
    ) { inherit pkgs; })
  ];
}
