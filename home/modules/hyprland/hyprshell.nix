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

  # Override upstream hyprshell service for compatibility
  systemd.user.services.hyprshell = {
    Unit = {
      # mkForce required to override upstream module's PartOf
      # Prevents service stopping during home-manager reload
      PartOf = pkgs.lib.mkForce [ ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };
    Service = {
      ExecStartPre = "${waitForHyprland}";
      RestartSec = 2;
      # Cairo renderer fixes invisible windows on NixOS
      Environment = [ "GSK_RENDERER=cairo" ];
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

    # Base styling with theme colors imported from omarchy
    styleFile = ''
      /* Default styling variables */
      * {
          --border-radius: 12px;
          --border-size: 3px;
          --border-style: solid;
          --window-padding: 8px;
      }

      /* Import theme colors from omarchy (overrides defaults) */
      @import url("${config.home.homeDirectory}/.config/omarchy/current/theme/hyprshell.css");

      .monitor {
          border: none;
      }
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
