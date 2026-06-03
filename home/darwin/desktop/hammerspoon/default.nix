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
      ".hammerspoon/workspace_grid_persistence.lua".source = ./workspace_grid_persistence.lua;
      ".hammerspoon/workspace_grid_menubar.lua".source = ./workspace_grid_menubar.lua;
      ".hammerspoon/switcher_bridge.lua".source = ./switcher_bridge.lua;
    };

    # Stop Hammerspoon popping its Console window every launch/reload (a config
    # redeploy on rebuild triggers a reload).
    activation.suppressHammerspoonConsoleAtLaunch = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      /usr/bin/defaults write org.hammerspoon.Hammerspoon MJShowWindowAtLaunchKey -bool false
    '';
  };
}
