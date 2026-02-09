{ pkgs, ... }:
let
  # Custom fork of clipse
  clipse-zanoni = pkgs.buildGoModule {
    pname = "clipse";
    version = "zanoni.v1.2.1";

    src = pkgs.fetchFromGitHub {
      owner = "castrozan";
      repo = "clipse";
      rev = "eb51f2e892b5ca36aaade414fd2c11059aa72326";
      sha256 = "sha256-DKkvE9tuj8cXt2uuiGjWJ4KrfU6hqRqT/SoE/f+Gst4=";
    };

    vendorHash = "sha256-LxwST4Zjxq6Fwc47VeOdv19J3g/DHZ7Fywp2ZvVR06I=";
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
