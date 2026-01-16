{ pkgs, ... }:
let
  # Custom fork of clipse with fixes
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
    proxyVendor = true; # Use Go module proxy instead of vendor dir

    buildInputs = with pkgs; [ xorg.libX11 xorg.libXtst ];
    nativeBuildInputs = with pkgs; [ pkg-config ];

    # Build with wayland tag for Wayland support
    tags = [ "wayland" ];

    meta = with pkgs.lib; {
      description = "Clipboard manager for Wayland (custom fork)";
      homepage = "https://github.com/castrozan/clipse";
      license = licenses.mit;
    };
  };

  # GNOME Wayland listener - polling based since wl-paste --watch doesn't work on GNOME
  clipse-listen = pkgs.writeShellScriptBin "clipse-listen" ''
    LAST_HASH=""
    POLL_INTERVAL=1

    while true; do
      # Get current clipboard content
      CONTENT=$(${pkgs.wl-clipboard}/bin/wl-paste --no-newline 2>/dev/null || echo "")

      if [ -n "$CONTENT" ]; then
        # Hash the content to detect changes
        CURRENT_HASH=$(echo -n "$CONTENT" | md5sum | cut -d' ' -f1)

        if [ "$CURRENT_HASH" != "$LAST_HASH" ]; then
          # New clipboard content - store it
          echo "$CONTENT" | ${clipse-zanoni}/bin/clipse -wl-store 2>/dev/null
          LAST_HASH="$CURRENT_HASH"
        fi
      fi

      sleep $POLL_INTERVAL
    done
  '';

  # Wrapper script that opens clipse TUI and restarts listener after
  clipse-tui = pkgs.writeShellScriptBin "clipse-tui" ''
    # -fc $PPID forces terminal to close after selection
    ${clipse-zanoni}/bin/clipse -fc $PPID
    # Restart the listener after TUI closes (TUI kills it)
    systemctl --user restart clipse.service &
  '';
in
{
  home.packages = [
    pkgs.wl-clipboard
    clipse-zanoni
    clipse-tui
    clipse-listen
  ];

  # Configure clipse as a systemd user service to run in the background
  systemd.user.services.clipse = {
    Unit = {
      Description = "Clipse clipboard manager";
      After = [ "graphical-session.target" ];
      PartOf = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${clipse-listen}/bin/clipse-listen";
      Restart = "on-failure";
      RestartSec = "5s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };

  systemd.user.startServices = "sd-switch";
}
