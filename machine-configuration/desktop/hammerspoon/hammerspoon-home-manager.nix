{ config, pkgs, ... }:
{
  # Hammerspoon is notarized (Developer ID), so Sophos endpoint security trusts
  # it - unlike the ad-hoc-signed AeroSpace fork, whose disk access SophosCryptoGuard
  # holds, deadlocking it. init.lua reimplements the prior AeroSpace virtual-
  # workspace grid by show/hiding windows on a single macOS Space.
  home = {
    file = {
      ".hammerspoon/init.lua".source = ./init.lua;
      ".hammerspoon/workspace_grid.lua".source = ./workspace_grid.lua;
      ".hammerspoon/workspace_grid_menu_bar_reveal.lua".source = ./workspace_grid_menu_bar_reveal.lua;
      ".hammerspoon/workspace_grid_browser_aware_digit_keybindings.lua".source =
        ./workspace_grid_browser_aware_digit_keybindings.lua;
      ".hammerspoon/workspace_grid_navigation.lua".source = ./workspace_grid_navigation.lua;
      ".hammerspoon/workspace_grid_pinned_window.lua".source = ./workspace_grid_pinned_window.lua;
      ".hammerspoon/workspace_grid_two_window_tiling.lua".source = ./workspace_grid_two_window_tiling.lua;
      ".hammerspoon/workspace_grid_two_window_tiling_entry_points.lua".source =
        ./workspace_grid_two_window_tiling_entry_points.lua;
      ".hammerspoon/workspace_grid_two_window_tiling_hotkeys.lua".source =
        ./workspace_grid_two_window_tiling_hotkeys.lua;
      ".hammerspoon/workspace_grid_window_layout.lua".source = ./workspace_grid_window_layout.lua;
      ".hammerspoon/workspace_grid_window_assignment.lua".source = ./workspace_grid_window_assignment.lua;
      ".hammerspoon/workspace_grid_window_query.lua".source = ./workspace_grid_window_query.lua;
      ".hammerspoon/window_server_truncated_owner_name.lua".source =
        ./window_server_truncated_owner_name.lua;
      ".hammerspoon/window_server_on_screen_windows.lua".source = ./window_server_on_screen_windows.lua;
      ".hammerspoon/workspace_grid_window_snapshot.lua".source = ./workspace_grid_window_snapshot.lua;
      ".hammerspoon/workspace_grid_window_focus.lua".source = ./workspace_grid_window_focus.lua;
      ".hammerspoon/workspace_grid_window_menu.lua".source = ./workspace_grid_window_menu.lua;
      ".hammerspoon/workspace_grid_window_menu_bar_item.lua".source =
        ./workspace_grid_window_menu_bar_item.lua;
      ".hammerspoon/workspace_grid_window_events.lua".source = ./workspace_grid_window_events.lua;
      ".hammerspoon/workspace_grid_session_generation.lua".source =
        ./workspace_grid_session_generation.lua;
      ".hammerspoon/workspace_grid_summon.lua".source = ./workspace_grid_summon.lua;
      ".hammerspoon/workspace_grid_summon_to_workspace.lua".source =
        ./workspace_grid_summon_to_workspace.lua;
      ".hammerspoon/chrome_profile_window.lua".source = ./chrome_profile_window.lua;
      ".hammerspoon/wezterm_summon.lua".source = ./wezterm_summon.lua;
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
      ${pkgs.coreutils}/bin/timeout 5 /usr/bin/defaults write org.hammerspoon.Hammerspoon MJShowWindowAtLaunchKey -bool false 2>/dev/null || true
    '';
  };
}
