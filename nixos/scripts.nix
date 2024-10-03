{ pkgs, ... }:
{
  imports = [
    ./on.nix
    ./set-random-bg-kitty.nix
    ./game-shift.nix
  ];
}
