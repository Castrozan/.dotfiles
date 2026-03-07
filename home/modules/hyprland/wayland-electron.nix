_: {
  home.sessionVariables.NIXOS_OZONE_WL = "";

  xdg.configFile = {
    "cursor-flags.conf".text = ''
      --ozone-platform-hint=auto
      --enable-features=WaylandWindowDecorations
    '';
  };
}
