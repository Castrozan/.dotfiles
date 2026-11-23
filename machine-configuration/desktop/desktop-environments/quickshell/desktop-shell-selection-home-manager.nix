{ config, lib, ... }:
let
  inherit (config.custom.desktopShell) hyprlandBindings sessionServices;
in
{
  options.custom.desktopShell = {
    active = lib.mkOption {
      type = lib.types.enum [
        "quickshell-bar"
        "impasto"
      ];
      default = "quickshell-bar";
      description = "The one desktop shell the Hyprland session runs: its panels, launcher, notification daemon and key bindings.";
    };

    hyprlandBindings = lib.mkOption {
      type = lib.types.lines;
      default = "";
      description = "Hyprland bind lines owned by the active desktop shell.";
    };

    sessionServices = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Systemd user units the Hyprland session starts for the active desktop shell.";
    };
  };

  config.xdg.configFile = {
    "hypr-shell/bindings.conf".text = hyprlandBindings;
    "hypr-shell/autostart.conf".text = lib.optionalString (sessionServices != [ ]) ''
      exec-once = sleep 2 && systemctl --user start ${lib.concatStringsSep " " sessionServices}
    '';
  };
}
