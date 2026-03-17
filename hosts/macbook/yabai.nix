{
  services.yabai = {
    enable = true;
    config = {
      layout = "stack";
      top_padding = 4;
      bottom_padding = 10;
      left_padding = 10;
      right_padding = 10;
      window_gap = 10;
      auto_balance = "off";
      split_ratio = "0.5";
      window_placement = "second_child";
      focus_follows_mouse = "off";
      mouse_follows_focus = "off";
      mouse_modifier = "alt";
      mouse_action1 = "move";
      mouse_action2 = "resize";
    };
    extraConfig = ''
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
