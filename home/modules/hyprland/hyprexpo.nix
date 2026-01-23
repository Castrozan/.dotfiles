{ pkgs, inputs, ... }:
let
  hyprexpoPackage = inputs.hyprland-plugins.packages.${pkgs.stdenv.hostPlatform.system}.hyprexpo;
in
{
  home.file.".config/hyprexpo.conf".text = ''
    plugin = ${hyprexpoPackage}/lib/libhyprexpo.so

    plugin {
        hyprexpo {
            columns = 7
            gap_size = 5
            bg_col = rgb(1e1e1e)
            workspace_method = center current
            enable_gesture = true
            gesture_distance = 300
            gesture_positive = true
        }
    }

    # Workspace overview keybinding
    bindd = SUPER, J, Workspace overview, hyprexpo:expo, toggle
  '';
}
