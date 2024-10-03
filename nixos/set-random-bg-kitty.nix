# Script to set a random background image in Kitty terminal
{ pkgs, ... }:

let
  set-random-bg-kitty = pkgs.writeShellScriptBin "set-random-bg-kitty" ''
    #!/usr/bin/env bash

    # Directory containing background images
    IMAGE_DIR="$HOME/.dotfiles-nixos/images"

    # Select a random image from the directory
    RANDOM_IMAGE=$(find "$IMAGE_DIR" -type f | shuf -n 1)

    # Set the selected image as the background in Kitty
    kitty @ set-background-image "$RANDOM_IMAGE"
  '';

in
{
  environment.systemPackages = [ set-random-bg-kitty ];
}
