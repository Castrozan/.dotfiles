{ pkgs, ... }:
{
  home.packages = [
    (import ./image-package.nix { inherit pkgs; })
    (import ./movie-package.nix { inherit pkgs; })
    (import ./speech-package.nix { inherit pkgs; })
    (import ./video-package.nix { inherit pkgs; })
  ];
}
