{ pkgs, inputs, ... }:
{
  imports = [ inputs.hyprshell.homeModules.hyprshell ];

  programs.hyprshell = {
    enable = true;
    # Use flake package to match Hyprland 0.53.0
    package = inputs.hyprshell.packages.${pkgs.stdenv.hostPlatform.system}.hyprshell;

    systemd = {
      enable = true;
      target = "hyprland-session.target";
    };

    settings = {
      windows = {
        enable = true;
        scale = 8.5;
        items_per_row = 5;

        # Alt+Tab window switcher
        switch = {
          enable = true;
          key = "Tab";
          modifier = "alt";
          filter_by = [ ];
          switch_workspaces = false;
        };

        # Super+Tab window switcher
        switch_2 = {
          enable = true;
          key = "Tab";
          modifier = "super";
          filter_by = [ ];
          switch_workspaces = false;
        };
      };
    };
  };
}
