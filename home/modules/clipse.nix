{ pkgs, ... }:
let
  # Custom fork of clipse
  clipse-zanoni = pkgs.buildGoModule {
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

    buildInputs = with pkgs; [
      xorg.libX11
      xorg.libXtst
    ];
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
  # NOTE: On GNOME Wayland, wl-paste --watch doesn't work (requires wlroots protocol)
  # See docs/clipse-gnome-issues.md for details and alternatives
  home.packages = [
    pkgs.wl-clipboard
    clipse-zanoni
  ];

  # Background clipboard listener service
  # Works on wlroots compositors (Hyprland, Sway), limited on GNOME
  systemd.user.services.clipse = {
    Unit = {
      Description = "Clipse clipboard manager listener";
      After = [ "graphical-session.target" ];
      StartLimitIntervalSec = 30;
      StartLimitBurst = 3;
    };
    Service = {
      Type = "simple";
      ExecStart = "${clipse-zanoni}/bin/clipse --listen-shell";
      Restart = "always";
      RestartSec = 5;
    };
    Install.WantedBy = [ "graphical-session.target" ];
  };
}
