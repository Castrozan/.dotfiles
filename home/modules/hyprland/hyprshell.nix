{
  pkgs,
  inputs,
  config,
  ...
}:
let
  waitForHyprland = pkgs.writeShellScript "wait-for-hyprland" ''
    for i in $(seq 1 50); do
      if hyprctl monitors &>/dev/null; then
        exit 0
      fi
      sleep 0.2
    done
    echo "Hyprland not ready after 10s, starting anyway"
  '';
in
{
  imports = [ inputs.hyprshell.homeModules.hyprshell ];

  # Override systemd service to wait for Hyprland IPC
  systemd.user.services.hyprshell = {
    Service = {
      ExecStartPre = "${waitForHyprland}";
      RestartSec = 2;
    };
  };

  programs.hyprshell = {
    enable = true;
    # Use flake package to match Hyprland 0.53.0
    package = inputs.hyprshell.packages.${pkgs.stdenv.hostPlatform.system}.hyprshell;

    systemd = {
      enable = true;
      target = "hyprland-session.target";
    };

    # Use dynamic theme CSS from omarchy theme system via @import
    styleFile = ''
      @import url("${config.home.homeDirectory}/.config/omarchy/current/theme/hyprshell.css");
    '';

    settings = {
      windows = {
        enable = true;
        scale = 8.5;
        items_per_row = 5;

        # Super+Tab window switcher (current workspace only)
        switch = {
          enable = true;
          key = "Tab";
          modifier = "super";
          filter_by = [ "current_workspace" ];
          switch_workspaces = false;
        };
      };
    };
  };
}
