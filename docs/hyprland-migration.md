# Migrating from GNOME to Hyprland on NixOS

## Why Hyprland?

- Native wlroots compositor - full `wl-paste --watch` support
- Clipse works perfectly with background monitoring
- Tiling window manager with smooth animations
- Highly configurable

## Prerequisites

- NixOS with flakes enabled
- Backup current GNOME config

## Installation Steps

### 1. Add Hyprland to System Configuration

```nix
# nixos/hosts/dellg15/configuration.nix
{ pkgs, ... }:
{
  programs.hyprland = {
    enable = true;
    xwayland.enable = true;
  };

  # Optional: keep GNOME as fallback
  services.xserver = {
    enable = true;
    displayManager.gdm.enable = true;
    desktopManager.gnome.enable = true;  # Keep for fallback
  };

  # Required packages
  environment.systemPackages = with pkgs; [
    kitty           # Terminal (or wezterm)
    wofi            # App launcher
    waybar          # Status bar
    swww            # Wallpaper
    grim            # Screenshot
    slurp           # Region selection
    wl-clipboard    # Clipboard (works with clipse!)
    mako            # Notifications
  ];
}
```

### 2. Home-Manager Hyprland Config

```nix
# home/modules/hyprland.nix
{ pkgs, ... }:
{
  wayland.windowManager.hyprland = {
    enable = true;
    settings = {
      "$mod" = "SUPER";

      bind = [
        "$mod, Return, exec, wezterm"
        "$mod, Q, killactive"
        "$mod, D, exec, wofi --show drun"
        "$mod, V, exec, wezterm start -- clipse"  # Clipse works!
        "$mod, E, exec, nautilus"
        "$mod, F, fullscreen"
        "$mod, Space, togglefloating"

        # Workspaces
        "$mod, 1, workspace, 1"
        "$mod, 2, workspace, 2"
        "$mod, 3, workspace, 3"
        # ... etc
      ];

      monitor = [
        # Dell G15 laptop display + external
        "eDP-1, 1920x1080@144, 0x0, 1"
        ", preferred, auto, 1"  # Any external monitor
      ];

      input = {
        kb_layout = "br";
        follow_mouse = 1;
        touchpad = {
          natural_scroll = true;
        };
      };

      general = {
        gaps_in = 5;
        gaps_out = 10;
        border_size = 2;
        "col.active_border" = "rgba(33ccffee)";
      };

      decoration = {
        rounding = 10;
        blur = {
          enabled = true;
          size = 3;
        };
      };
    };
  };

  # Waybar config
  programs.waybar = {
    enable = true;
    settings = [{
      layer = "top";
      modules-left = ["hyprland/workspaces"];
      modules-center = ["clock"];
      modules-right = ["battery" "network" "pulseaudio"];
    }];
  };
}
```

### 3. Import in User Config

```nix
# users/lucas.zanoni/home.nix
{
  imports = [
    # ... existing imports
    ../../home/modules/hyprland.nix
  ];
}
```

### 4. Rebuild and Test

```bash
sudo nixos-rebuild switch --flake .#dellg15

# Logout of GNOME, select Hyprland from GDM
```

## Clipse on Hyprland

With Hyprland, clipse works perfectly:

```nix
# home/modules/clipse.nix - Full version with systemd service
{ pkgs, ... }:
{
  home.packages = [ pkgs.wl-clipboard ];

  systemd.user.services.clipse = {
    Unit = {
      Description = "Clipse clipboard manager";
      After = [ "graphical-session.target" ];
    };
    Service = {
      Type = "simple";
      ExecStart = "${pkgs.clipse}/bin/clipse --listen-shell";
      Restart = "always";
    };
    Install.WantedBy = [ "graphical-session.target" ];
  };
}
```

## Keeping Both (Dual Setup)

You can keep both GNOME and Hyprland:

```nix
# Conditional config based on session
{ lib, ... }:
let
  isHyprland = builtins.getEnv "XDG_CURRENT_DESKTOP" == "Hyprland";
in
{
  # Clipse service only on Hyprland
  systemd.user.services.clipse = lib.mkIf isHyprland {
    # ... service config
  };
}
```

## Essential Hyprland Keybindings

| Key | Action |
|-----|--------|
| Super+Return | Terminal |
| Super+Q | Close window |
| Super+D | App launcher |
| Super+V | Clipse (clipboard) |
| Super+1-9 | Switch workspace |
| Super+Shift+1-9 | Move window to workspace |
| Super+Mouse | Move/resize window |

## Resources

- [Hyprland Wiki](https://wiki.hyprland.org/)
- [NixOS Hyprland Module](https://wiki.hyprland.org/Nix/)
- [Hyprland GitHub](https://github.com/hyprwm/Hyprland)
