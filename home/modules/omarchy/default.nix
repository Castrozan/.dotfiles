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
      ghostty # Using wezterm instead
      kitty # Using wezterm instead
      chromium # Using brave instead
    ];
  };

  # Override default applications to use our preferred apps
  wayland.windowManager.hyprland.settings = {
    "$terminal" = lib.mkForce "wezterm";
    "$browser" = lib.mkForce "brave";
    "$fileManager" = lib.mkForce "nautilus --new-window";

    # Lower mouse sensitivity (current is 0, going to -0.3)
    input = {
      sensitivity = lib.mkForce (-0.3);
    };

    # Override autostart - remove commands that require packages not installed
    # (omarchy-nix expects nixosModule to be imported for these packages)
    exec-once = lib.mkForce [
      "mako" # notifications
      "clipse -listen" # clipboard (without wl-clip-persist)
    ];

    exec = lib.mkForce [
      "pkill -SIGUSR2 waybar || waybar"
    ];
  };

  # Add packages that omarchy autostart needs but aren't in homeManagerModule
  home.packages = with pkgs; [
    mako # notification daemon
    clipse # clipboard manager
    wl-clipboard # clipboard tools
  ];
}
