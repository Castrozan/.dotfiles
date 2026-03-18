{
  system.defaults.CustomUserPreferences."com.apple.WindowManager" = {
    EnableTiledWindowMargins = false;
    EnableTilingByEdgeDrag = false;
    EnableTilingOptionAccelerator = false;
    EnableTopTilingByEdgeDrag = false;
    EnableStandardClickToShowDesktop = false;
    GloballyEnabled = false;
    AppWindowGroupingBehavior = 1;
    AutoHide = false;
    HideDesktop = true;
    StandardHideWidgets = false;
    StageManagerHideWidgets = false;
  };

  services.yabai = {
    enable = true;
    extraConfig = ''
      #!/bin/sh
      yabai -m config layout float
      yabai -m config top_padding 0
      yabai -m config bottom_padding 0
      yabai -m config left_padding 0
      yabai -m config right_padding 0
      yabai -m config window_gap 0
      yabai -m config auto_balance off
      yabai -m config split_ratio 0.5
      yabai -m config window_placement second_child
      yabai -m config focus_follows_mouse off
      yabai -m config mouse_follows_focus off
      yabai -m config mouse_modifier alt
      yabai -m config mouse_action1 move
      yabai -m config mouse_action2 resize

      yabai -m rule --add app="^System Settings$" manage=off
      yabai -m rule --add app="^System Preferences$" manage=off
      yabai -m rule --add app="^System Information$" manage=off
      yabai -m rule --add app="^Calculator$" manage=off
      yabai -m rule --add app="^Karabiner" manage=off
      yabai -m rule --add app="^Archive Utility$" manage=off
      yabai -m rule --add app="^Finder$" manage=off
      yabai -m rule --add app="^Activity Monitor$" manage=off
      yabai -m rule --add app="^Disk Utility$" manage=off
      yabai -m rule --add app="^Installer$" manage=off
      yabai -m rule --add app="^KeyboardSetupAssistant$" manage=off
      yabai -m rule --add app="^Font Book$" manage=off
      yabai -m rule --add app="^Spaceman$" manage=off
    '';
  };
}
