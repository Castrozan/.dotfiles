{ pkgs, ... }:
let
  python = pkgs.python312;
  virtualenvPath = "$HOME/.local/share/youtube-cli-venv";

  youtubeCliSource = pkgs.writeText "youtube-cli.py" (
    builtins.readFile ../../agents/skills/youtube/scripts/youtube-cli.py
  );

  youtubeCliSetupSource = pkgs.writeText "youtube-cli-setup.sh" (
    builtins.readFile ../../agents/skills/youtube/scripts/youtube-cli-setup.sh
  );

  youtubeCli = pkgs.writeShellScriptBin "youtube-cli" ''
    set -euo pipefail

    # Special command: setup OAuth credentials
    if [ "''${1:-}" = "setup" ]; then
      exec ${pkgs.bash}/bin/bash "${youtubeCliSetupSource}"
    fi

    VENV="${virtualenvPath}"

    if [ ! -f "$VENV/bin/python" ] || ! "$VENV/bin/pip" show google-api-python-client &>/dev/null; then
      echo "[nix] Installing youtube-cli dependencies..." >&2
      ${python}/bin/python -m venv "$VENV" 2>/dev/null || true
      "$VENV/bin/pip" install --quiet --upgrade \
        google-api-python-client \
        google-auth-oauthlib \
        google-auth-httplib2 >&2
    fi

    exec "$VENV/bin/python" "${youtubeCliSource}" "$@"
  '';
in
{
  home.packages = [ youtubeCli ];
}
