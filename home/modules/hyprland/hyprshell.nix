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
