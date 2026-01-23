{ pkgs, inputs, ... }:
let
  isNixOS = builtins.pathExists /etc/NIXOS;

  # On non-NixOS we need nixGL to provide GPU driver compatibility
  # Hyprland crashes without this due to GBM/Mesa mismatch
  hyprlandPackage =
    if isNixOS then
      pkgs.hyprland
    else
      let
        nixGLWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLIntel;
        hyprland-gl = pkgs.writeShellScriptBin "Hyprland" ''
          exec ${nixGLWrapper}/bin/nixGLIntel ${pkgs.hyprland}/bin/Hyprland "$@"
        '';
        hyprland-lowercase-gl = pkgs.writeShellScriptBin "hyprland" ''
          exec ${nixGLWrapper}/bin/nixGLIntel ${pkgs.hyprland}/bin/Hyprland "$@"
        '';
        hyprctl-gl = pkgs.writeShellScriptBin "hyprctl" ''
          exec ${pkgs.hyprland}/bin/hyprctl "$@"
        '';
        hyprland-wrapped = pkgs.symlinkJoin {
          name = "hyprland-wrapped";
          paths = [
            hyprland-gl
            hyprland-lowercase-gl
            hyprctl-gl
            pkgs.hyprland
          ];
        };
      in
      hyprland-wrapped;
in
{
  imports = [
    ./omarchy-scripts.nix
    ../fuzzel.nix
  ];

  home = {
    file = {
      ".config/hypr".source = ../../../.config/hypr;
      ".config/waybar".source = ../../../.config/waybar;

      # Omarchy theme system - symlink read-only parts, let 'current' be runtime-writable
      ".config/omarchy/themes".source = ../../../.config/omarchy/themes;
      ".config/omarchy/themed".source = ../../../.config/omarchy/themed;
    };

    # Initialize omarchy theme directory structure
    activation.initOmarchyTheme = ''
      mkdir -p $HOME/.config/omarchy/current/theme
      mkdir -p $HOME/.config/omarchy/user-themes
      mkdir -p $HOME/.config/omarchy/backgrounds
      touch $HOME/.config/omarchy/current/theme/hyprland.conf
    '';

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
      hyprlock
      hypridle

      # Media & volume
      playerctl
      pamixer

      # Status bar
      waybar

      # OSD for volume/brightness (omarchy feature)
      swayosd

      # Emoji picker
      bemoji

      # YAML/JSON processing (for theme templates)
      yq-go

      # Screenshot tools
      hyprshot
      grim
      slurp
      satty

      # Screen recording
      wf-recorder

      # Clipboard history
      cliphist

      # Color picker
      hyprpicker

      # JSON processing (for hyprctl scripts)
      jq

      # Logout menu
      wlogout

      # Polkit agent
      polkit_gnome

      # Calculator
      gnome-calculator

      # Bluetooth manager
      blueman

      # Audio control
      pavucontrol
    ]);
  };
}
