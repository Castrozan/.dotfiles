{ inputs, pkgs, ... }:
{
  # Add xkeyboard-config to fix dependency issue
  home.packages = with pkgs; [
    xkeyboard_config
    # Try caelestia package with dependency fix
    inputs.caelestia-shell.packages.${pkgs.system}.default
  ];

  programs.caelestia = {
    enable = true;
    systemd = {
      enable = false; # if you prefer starting from your compositor
      target = "graphical-session.target";
      environment = [ ];
    };
    settings = {
      bar.status = {
        showBattery = false;
      };
      paths.wallpaperDir = "~/Images";
    };
    cli = {
      enable = true; # Also add caelestia-cli to path
      settings = {
        theme.enableGtk = false;
      };
    };
  };
}
