{ config, ... }:
{
  # Hammerspoon is notarized (Developer ID), so Sophos endpoint security trusts
  # it - unlike the ad-hoc-signed AeroSpace fork, whose disk access SophosCryptoGuard
  # holds, deadlocking it. init.lua reimplements the prior AeroSpace virtual-
  # workspace grid by show/hiding windows on a single macOS Space.
  home = {
    file = {
      ".hammerspoon/init.lua".source = ./init.lua;
      ".hammerspoon/workspace_grid.lua".source = ./workspace_grid.lua;
      ".hammerspoon/workspace_grid_navigation.lua".source = ./workspace_grid_navigation.lua;
      ".hammerspoon/workspace_grid_pinned_window.lua".source = ./workspace_grid_pinned_window.lua;
      ".hammerspoon/workspace_grid_window_layout.lua".source = ./workspace_grid_window_layout.lua;
      ".hammerspoon/workspace_grid_window_assignment.lua".source = ./workspace_grid_window_assignment.lua;
      ".hammerspoon/workspace_grid_window_query.lua".source = ./workspace_grid_window_query.lua;
      ".hammerspoon/workspace_grid_session_generation.lua".source =
        ./workspace_grid_session_generation.lua;
      ".hammerspoon/workspace_grid_summon.lua".source = ./workspace_grid_summon.lua;
      ".hammerspoon/workspace_grid_summon_to_workspace.lua".source =
        ./workspace_grid_summon_to_workspace.lua;
      ".hammerspoon/chrome_profile_window.lua".source = ./chrome_profile_window.lua;
      ".hammerspoon/workspace_grid_persistence.lua".source = ./workspace_grid_persistence.lua;
      ".hammerspoon/workspace_grid_menubar.lua".source = ./workspace_grid_menubar.lua;
      ".hammerspoon/switcher_bridge.lua".source = ./switcher_bridge.lua;
      ".hammerspoon/prevent_window_minimize.lua".source = ./prevent_window_minimize.lua;
      ".hammerspoon/karabiner_application_focus_variables.lua".source =
        ./karabiner_application_focus_variables.lua;
      ".hammerspoon/smart_home_media_key_control.lua".text =
        builtins.replaceStrings
          [ "@USER_BIN_PATH@" ]
          [ "/etc/profiles/per-user/${config.home.username}/bin" ]
          (builtins.readFile ./smart_home_media_key_control.lua);
    };

    # Stop Hammerspoon popping its Console window every launch/reload (a config
    # redeploy on rebuild triggers a reload).
    activation.suppressHammerspoonConsoleAtLaunch = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      /usr/bin/defaults write org.hammerspoon.Hammerspoon MJShowWindowAtLaunchKey -bool false
    '';
  };
}
