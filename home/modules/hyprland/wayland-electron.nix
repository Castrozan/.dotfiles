{ ... }:
{
  # Disable nixpkgs wrapper flag injection — env vars handle Wayland
  # without triggering Electron's "not in known options" warnings
  home.sessionVariables.NIXOS_OZONE_WL = "";

  xdg.configFile = {
    # Cursor is an AppImage without nixpkgs wrapper
    "cursor-flags.conf".text = ''
      --ozone-platform-hint=auto
      --enable-features=WaylandWindowDecorations
    '';
  };
}
