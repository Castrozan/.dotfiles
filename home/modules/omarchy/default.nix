{
  config,
  pkgs,
  lib,
  inputs,
  ...
}:
let
  system = pkgs.stdenv.hostPlatform.system;
in
{
  imports = [
    inputs.omarchy-nix.homeManagerModules.default
  ];

  omarchy = {
    full_name = "Lucas Zanoni";
    email_address = "lucas@zanoni.dev";
    theme = "catppuccin";
    scale = 1;
    monitors = [ "HDMI-A-1" ];

    # Exclude packages we already have configured elsewhere
    exclude_packages = with pkgs; [
      ghostty # Using kitty instead
      chromium # Using brave instead
    ];
  };

  # Override default applications to use our preferred apps
  wayland.windowManager.hyprland.settings = {
    "$terminal" = lib.mkForce "kitty";
    "$browser" = lib.mkForce "brave";
    "$fileManager" = lib.mkForce "nautilus --new-window";

    # Lower mouse sensitivity (current is 0, going to -0.3)
    input = {
      sensitivity = lib.mkForce (-0.3);
    };
  };
}
