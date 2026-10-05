{ pkgs, ... }:
{
  home.packages = [
    (import ./speech-package.nix { inherit pkgs; })
    (import ./video-package.nix { inherit pkgs; })
  ];
}
