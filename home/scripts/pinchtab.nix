{ pkgs, ... }:
let
  pinchtabBinary = pkgs.buildGoModule {
    pname = "pinchtab";
    version = "0.4.0";

    src = pkgs.fetchFromGitHub {
      owner = "pinchtab";
      repo = "pinchtab";
      rev = "9e604eb";
      hash = "sha256-7hU++NCqs3vgLTOHP4a7fLm5akv0cc+rdYwqWpDEq24=";
    };

    vendorHash = "sha256-ZXocuugti6YOxV7p/4nqu1voEhf+HxYYaeWId0SYZ64=";
  };

  pinchtab = pkgs.writeShellScriptBin "pinchtab" ''
    set -euo pipefail

    export PATH="${pkgs.chromium}/bin:$PATH"

    if [[ -z "''${WAYLAND_DISPLAY:-}" ]] && [[ -d "/run/user/''${UID:-1000}" ]]; then
      for candidate in wayland-1 wayland-0; do
        if [[ -e "/run/user/''${UID:-1000}/''${candidate}" ]]; then
          export WAYLAND_DISPLAY="$candidate"
          break
        fi
      done
    fi
    if [[ -z "''${DISPLAY:-}" ]]; then
      export DISPLAY=":0"
    fi
    if [[ -n "''${WAYLAND_DISPLAY:-}" ]] && [[ -z "''${NIXOS_OZONE_WL:-}" ]]; then
      export NIXOS_OZONE_WL=1
    fi

    export CHROME_FLAGS="--ozone-platform=wayland ''${CHROME_FLAGS:-}"
    export BRIDGE_HEADLESS="''${BRIDGE_HEADLESS:-true}"
    export BRIDGE_PROFILE="''${BRIDGE_PROFILE:-$HOME/.pinchtab/chrome-profile}"
    export BRIDGE_STATE_DIR="''${BRIDGE_STATE_DIR:-$HOME/.pinchtab}"
    export CHROME_BINARY="$(command -v chromium)"

    exec ${pinchtabBinary}/bin/pinchtab "$@"
  '';
in
{
  home.packages = [ pinchtab ];
}
