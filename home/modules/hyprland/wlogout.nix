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
        action = "hyprctl dispatch exit";
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
      # TODO: suspend is not locking the screen before suspending
      {
        label = "suspend";
        action = "systemctl suspend";
        text = "Suspend";
        keybind = "U";
      }
    ];
  };
}
