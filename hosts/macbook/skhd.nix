{
  services.skhd = {
    enable = true;
    skhdConfig = ''
      # Move focused window to space and follow focus
      cmd + shift - 1 : yabai -m window --space 1 --focus
      cmd + shift - 2 : yabai -m window --space 2 --focus
      cmd + shift - 3 : yabai -m window --space 3 --focus
      cmd + shift - 4 : yabai -m window --space 4 --focus
      cmd + shift - 5 : yabai -m window --space 5 --focus
      cmd + shift - 6 : yabai -m window --space 6 --focus
      cmd + shift - 7 : yabai -m window --space 7 --focus

      # Move focused window to space silently (no focus switch)
      cmd + alt - 1 : yabai -m window --space 1
      cmd + alt - 2 : yabai -m window --space 2
      cmd + alt - 3 : yabai -m window --space 3
      cmd + alt - 4 : yabai -m window --space 4
      cmd + alt - 5 : yabai -m window --space 5
      cmd + alt - 6 : yabai -m window --space 6
      cmd + alt - 7 : yabai -m window --space 7

      # Toggle zoom-fullscreen (fill screen ignoring gaps)
      cmd - f : yabai -m window --toggle zoom-fullscreen

      # Toggle layout: stack (grouped-maximized) / bsp (tiled)
      cmd - t : yabai -m space --layout "$(yabai -m query --spaces --space | jq -r 'if .type == "stack" then "bsp" else "stack" end')"

      # Focus: cycle stack in stack mode, directional in bsp mode
      cmd - left : layout=$(yabai -m query --spaces --space | jq -r '.type'); \
                   if [ "$layout" = "stack" ]; then \
                     yabai -m window --focus stack.prev || yabai -m window --focus stack.last; \
                   else \
                     yabai -m window --focus west || yabai -m window --focus east; \
                   fi

      cmd - right : layout=$(yabai -m query --spaces --space | jq -r '.type'); \
                    if [ "$layout" = "stack" ]; then \
                      yabai -m window --focus stack.next || yabai -m window --focus stack.first; \
                    else \
                      yabai -m window --focus east || yabai -m window --focus west; \
                    fi

      cmd - up : yabai -m window --focus north || yabai -m window --focus south
      cmd - down : yabai -m window --focus south || yabai -m window --focus north

      # Resize windows (useful in bsp mode)
      cmd + shift - right : yabai -m window --resize right:100:0 2>/dev/null || yabai -m window --resize left:100:0
      cmd + shift - left  : yabai -m window --resize left:-100:0 2>/dev/null || yabai -m window --resize right:-100:0
      cmd + shift - down  : yabai -m window --resize bottom:0:100 2>/dev/null || yabai -m window --resize top:0:100
      cmd + shift - up    : yabai -m window --resize top:0:-100 2>/dev/null || yabai -m window --resize bottom:0:-100

      # Toggle float for focused window
      cmd + shift - space : yabai -m window --toggle float; yabai -m window --grid 4:4:1:1:2:2
    '';
  };
}
