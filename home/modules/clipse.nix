{ pkgs, ... }:
let
  # Custom fork of clipse
  clipse-zanoni = pkgs.buildGoModule rec {
    pname = "clipse";
    version = "zanoni.v1.2.0";

    src = pkgs.fetchFromGitHub {
      owner = "castrozan";
      repo = "clipse";
      rev = "73c6642206f7a1d1f4ac31f344f2851f9f6de0e6";
      sha256 = "02jpaav63h3c99d4f7zb7xi6zvbihggk66a9czdbfwxfa84c32zn";
    };

    vendorHash = "sha256-NGY8WBPxufHArOzz3MDr6r24xPLYPomWUEVOjlOU6pA=";
    proxyVendor = true;

    buildInputs = with pkgs; [ xorg.libX11 xorg.libXtst ];
    nativeBuildInputs = with pkgs; [ pkg-config ];

    tags = [ "wayland" ];

    meta = with pkgs.lib; {
      description = "Clipboard manager for Wayland (custom fork)";
      homepage = "https://github.com/castrozan/clipse";
      license = licenses.mit;
    };
  };
in
{
  # On GNOME Wayland, background clipboard monitoring causes flickering issues
  # (wl-paste --watch doesn't work, polling causes problems)
  # Just use clipse TUI on-demand via Win+V keybinding
  home.packages = [
    pkgs.wl-clipboard
    clipse-zanoni
  ];
}
