{ pkgs, ... }:
let
  python = pkgs.python312;
  virtualenvPath = "$HOME/.local/share/youtube-cli-venv";

  youtubeCliSource = pkgs.writeText "youtube-cli.py" (
    builtins.readFile ../../agents/skills/youtube/scripts/youtube-cli.py
  );

  youtubeCli = pkgs.writeShellScriptBin "youtube-cli" ''
    set -euo pipefail

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
