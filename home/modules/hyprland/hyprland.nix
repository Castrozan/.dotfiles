{
  pkgs,
  inputs,
  config,
  ...
}:
let
  isNixOS = builtins.pathExists /etc/NIXOS;
  hyprlandFlake = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;

  # On non-NixOS we need nixGL to provide GPU driver compatibility
  # Hyprland crashes without this due to GBM/Mesa mismatch
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
  imports = [
    ./omarchy-scripts.nix
    ../fuzzel.nix
  ];

  home = {
    pointerCursor = {
      name = "Bibata-Modern-Classic";
      package = pkgs.bibata-cursors;
      size = 24;
      gtk.enable = true;
      x11.enable = true;
    };

    file = {
      ".config/hypr".source = ../../../.config/hypr;

      # Waybar config - individual files so we can template style.css
      ".config/waybar/config".source = ../../../.config/waybar/config;
      ".config/waybar/nix.svg".source = ../../../.config/waybar/nix.svg;
      ".config/waybar/calendar-popup.py".source = ../../../.config/waybar/calendar-popup.py;
      ".config/waybar/calendar-toggle.sh".source = ../../../.config/waybar/calendar-toggle.sh;
      ".config/waybar/waybar-theme.css".source = ../../../.config/waybar/waybar-theme.css;
      # style.css with dynamic home directory path
      ".config/waybar/style.css".text =
        builtins.replaceStrings [ "@HOME@" ] [ config.home.homeDirectory ]
          (builtins.readFile ../../../.config/waybar/style.css.in);

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

      # Calendar popup for waybar
      yad

      # Bluetooth manager
      blueman

      # Audio control
      pavucontrol
    ]);
  };
}
