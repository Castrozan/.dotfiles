{ pkgs, ... }:
let
  mkScript = name: file: pkgs.writeShellScriptBin name (builtins.readFile file);
in
{
  home.packages = [
    (mkScript "omarchy-theme-set" ../../../bin/omarchy/theme-set)
    (mkScript "omarchy-theme-set-templates" ../../../bin/omarchy/theme-set-templates)
    (mkScript "omarchy-theme-bg-next" ../../../bin/omarchy/theme-bg-next)
    (mkScript "omarchy-theme-list" ../../../bin/omarchy/theme-list)
    (mkScript "omarchy-theme-current" ../../../bin/omarchy/theme-current)
    (mkScript "omarchy-theme-set-gnome" ../../../bin/omarchy/theme-set-gnome)
    (mkScript "omarchy-restart-waybar" ../../../bin/omarchy/restart-waybar)
    (mkScript "omarchy-restart-swayosd" ../../../bin/omarchy/restart-swayosd)
    (mkScript "omarchy-restart-hyprctl" ../../../bin/omarchy/restart-hyprctl)
    (mkScript "omarchy-restart-mako" ../../../bin/omarchy/restart-mako)
    (mkScript "omarchy-menu" ../../../bin/omarchy/menu)
    (mkScript "omarchy-super-launcher" ../../../bin/omarchy/super-launcher)
    (mkScript "omarchy-bluetooth" ../../../bin/omarchy/bluetooth)
  ];
}
