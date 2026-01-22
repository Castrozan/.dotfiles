{
  config,
  pkgs,
  lib,
  inputs,
  ...
}:
{
  imports = [
    inputs.omarchy-nix.homeManagerModules.default
  ];

  omarchy = {
    full_name = lib.mkForce "Lucas Zanoni";
    email_address = lib.mkForce "lucas@zanoni.dev";
    theme = lib.mkForce "tokyo-night"; # catppuccin-macchiato is incomplete in omarchy-nix
    scale = lib.mkForce 1;
    monitors = lib.mkForce [ "HDMI-A-1" ];

    # Exclude packages we already have configured elsewhere
    exclude_packages = lib.mkForce (
      with pkgs;
      [
        ghostty # Using wezterm instead
        kitty # Using wezterm instead
        chromium # Using brave instead
      ]
    );
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

    # Override clipse keybinding to use wezterm instead of ghostty
    bind = lib.mkAfter [
      "CTRL SUPER, V, exec, wezterm start --class clipse -e clipse"
    ];
  };

  # Add packages that omarchy autostart needs but aren't in homeManagerModule
  home.packages = with pkgs; [
    mako # notification daemon
    clipse # clipboard manager
    wl-clipboard # clipboard tools
    blueberry # bluetooth manager for waybar click handler
  ];

  # Override waybar on-click commands that use ghostty
  programs.waybar.settings = lib.mkForce [
    {
      layer = "top";
      position = "top";
      spacing = 0;
      height = 26;
      modules-left = [ "hyprland/workspaces" ];
      modules-center = [ "clock" ];
      modules-right = [
        "tray"
        "bluetooth"
        "network"
        "wireplumber"
        "cpu"
        "power-profiles-daemon"
        "battery"
      ];
      "hyprland/workspaces" = {
        on-click = "activate";
        format = "{icon}";
        format-icons = {
          default = "";
          "1" = "1";
          "2" = "2";
          "3" = "3";
          "4" = "4";
          "5" = "5";
          active = "󱓻";
        };
        persistent-workspaces = {
          "1" = [ ];
          "2" = [ ];
          "3" = [ ];
          "4" = [ ];
          "5" = [ ];
        };
      };
      cpu = {
        interval = 5;
        format = "󰍛";
        on-click = "wezterm -e btop"; # Changed from ghostty
      };
      clock = {
        format = "{:%A %I:%M %p}";
        format-alt = "{:%d %B W%V %Y}";
        tooltip = false;
      };
      network = {
        format-icons = [
          "󰤯"
          "󰤟"
          "󰤢"
          "󰤥"
          "󰤨"
        ];
        format = "{icon}";
        format-wifi = "{icon}";
        format-ethernet = "󰀂";
        format-disconnected = "󰖪";
        tooltip-format-wifi = "{essid} ({frequency} GHz)\n⇣{bandwidthDownBytes}  ⇡{bandwidthUpBytes}";
        tooltip-format-ethernet = "⇣{bandwidthDownBytes}  ⇡{bandwidthUpBytes}";
        tooltip-format-disconnected = "Disconnected";
        interval = 3;
        nospacing = 1;
        on-click = "wezterm -e nmtui"; # Changed from ghostty -e nmcli
      };
      battery = {
        interval = 5;
        format = "{capacity}% {icon}";
        format-discharging = "{icon}";
        format-charging = "{icon}";
        format-plugged = "";
        format-icons = {
          charging = [
            "󰢜"
            "󰂆"
            "󰂇"
            "󰂈"
            "󰢝"
            "󰂉"
            "󰢞"
            "󰂊"
            "󰂋"
            "󰂅"
          ];
          default = [
            "󰁺"
            "󰁻"
            "󰁼"
            "󰁽"
            "󰁾"
            "󰁿"
            "󰂀"
            "󰂁"
            "󰂂"
            "󰁹"
          ];
        };
        format-full = "Charged ";
        tooltip-format-discharging = "{power:>1.0f}W↓ {capacity}%";
        tooltip-format-charging = "{power:>1.0f}W↑ {capacity}%";
        states = {
          warning = 20;
          critical = 10;
        };
      };
      bluetooth = {
        format = "󰂯";
        format-disabled = "󰂲";
        format-connected = "";
        tooltip-format = "Devices connected: {num_connections}";
        on-click = "blueberry";
      };
      wireplumber = {
        format = "";
        format-muted = "󰝟";
        scroll-step = 5;
        on-click = "pavucontrol";
        tooltip-format = "Playing at {volume}%";
        on-click-right = "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle";
        max-volume = 150;
      };
      tray = {
        spacing = 13;
      };
      power-profiles-daemon = {
        format = "{icon}";
        tooltip-format = "Power profile: {profile}";
        tooltip = true;
        format-icons = {
          power-saver = "󰡳";
          balanced = "󰊚";
          performance = "󰡴";
        };
      };
    }
  ];
}
