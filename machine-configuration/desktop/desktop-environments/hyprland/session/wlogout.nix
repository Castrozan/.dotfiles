{ pkgs, ... }:
{
  programs.wlogout = {
    enable = true;
    package = pkgs.wlogout;
    layout = [
      {
        label = "lock";
        action = "hyprlock";
        text = "Lock";
        keybind = "L";
      }
      {
        label = "logout";
        action = "if uwsm check is-active; then uwsm stop; else hyprctl dispatch exit; fi";
        text = "Logout";
        keybind = "E";
      }
      {
        label = "shutdown";
        action = "systemctl poweroff";
        text = "Shutdown";
        keybind = "S";
      }
      {
        label = "reboot";
        action = "systemctl reboot";
        text = "Reboot";
        keybind = "R";
      }
      {
        label = "suspend";
        action = "systemctl suspend";
        text = "Suspend";
        keybind = "U";
      }
    ];
  };
}
