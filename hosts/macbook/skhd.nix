{
  services.skhd = {
    enable = true;
    skhdConfig = ''
      cmd + shift - 1 : yabai -m window --space 1 --focus
      cmd + shift - 2 : yabai -m window --space 2 --focus
      cmd + shift - 3 : yabai -m window --space 3 --focus
      cmd + shift - 4 : yabai -m window --space 4 --focus
      cmd + shift - 5 : yabai -m window --space 5 --focus
      cmd + shift - 6 : yabai -m window --space 6 --focus
      cmd + shift - 7 : yabai -m window --space 7 --focus

      cmd + alt - 1 : yabai -m window --space 1
      cmd + alt - 2 : yabai -m window --space 2
      cmd + alt - 3 : yabai -m window --space 3
      cmd + alt - 4 : yabai -m window --space 4
      cmd + alt - 5 : yabai -m window --space 5
      cmd + alt - 6 : yabai -m window --space 6
      cmd + alt - 7 : yabai -m window --space 7

      cmd - w : yabai -m window --close

      cmd - f : display_frame=$(yabai -m query --displays --display | python3 -c "import json,sys; d=json.load(sys.stdin)['frame']; print(f'{d[\"x\"]:.0f} {d[\"y\"]+25:.0f} {d[\"w\"]:.0f} {d[\"h\"]-25:.0f}')"); read x y w h <<< "$display_frame"; osascript -e "tell application \"System Events\" to tell (first process whose frontmost is true) to set {position, size} of window 1 to {{$x, $y}, {$w, $h}}"

    '';
  };
}
