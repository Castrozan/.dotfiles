{ pkgs }:
pkgs.lib.makeLibraryPath (
  with pkgs;
  [
    alsa-lib
    at-spi2-core
    cairo
    cups
    dbus
    expat
    glib
    libgbm
    libxkbcommon
    nspr
    nss
    pango
    systemdLibs
    xorg.libX11
    xorg.libXcomposite
    xorg.libXdamage
    xorg.libXext
    xorg.libXfixes
    xorg.libXrandr
    xorg.libXtst
    xorg.libxcb
  ]
)
