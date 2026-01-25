{ pkgs, inputs, ... }:
let
  isNixOS = builtins.pathExists /etc/NIXOS;
  hyprlandFlake = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;

  hyprlandPackage =
    if isNixOS then
      hyprlandFlake
    else
      let
        nixGLWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLIntel;
        hyprland-gl = pkgs.writeShellScriptBin "Hyprland" ''
          exec ${nixGLWrapper}/bin/nixGLIntel ${hyprlandFlake}/bin/Hyprland "$@"
        '';
        hyprland-lowercase-gl = pkgs.writeShellScriptBin "hyprland" ''
          exec ${nixGLWrapper}/bin/nixGLIntel ${hyprlandFlake}/bin/Hyprland "$@"
        '';
        hyprctl-gl = pkgs.writeShellScriptBin "hyprctl" ''
          exec ${hyprlandFlake}/bin/hyprctl "$@"
        '';
        hyprland-wrapped = pkgs.symlinkJoin {
          name = "hyprland-wrapped";
          paths = [
            hyprland-gl
            hyprland-lowercase-gl
            hyprctl-gl
            hyprlandFlake
          ];
        };
      in
      hyprland-wrapped;
in
{
  home = {
    # file.".config/hypr".source = ../../../.config/hypr;

    packages = [
      hyprlandPackage
    ]
    ++ (with pkgs; [
      # Wayland tools
      wl-clipboard

      # Wallpaper
      hyprpaper
      swaybg

      # Notifications
      mako
      libnotify

      # Lock screen and idle
      # hyprlock
      # hypridle

      # Media & volume
      playerctl
      pamixer

      # OSD for volume/brightness
      # swayosd

      # Emoji picker
      bemoji

      # Screenshot tools
      hyprshot
      grim
      slurp
      satty

      # Screen recording
      # wf-recorder

      # Clipboard history
      cliphist

      # Color picker
      hyprpicker

      # JSON processing
      jq

      # Logout menu
      # wlogout

      # Polkit agent
      polkit_gnome

      # Calculator
      gnome-calculator

      # Calendar popup helper
      # yad

      # Bluetooth manager
      blueman

      # Audio control
      pavucontrol
    ]);
  };
}
