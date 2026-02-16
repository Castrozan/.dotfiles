{ pkgs, ... }:
let
  python = pkgs.python312;
  version = "0.3.0";
  virtualenvPath = "$HOME/.local/share/openclaw-dash-venv";

  openclawDash = pkgs.writeShellScriptBin "openclaw-dash" ''
    set -euo pipefail

    VENV="${virtualenvPath}"

    if [ ! -f "$VENV/bin/openclaw-dash" ] || ! "$VENV/bin/pip" show openclaw-dash 2>/dev/null | grep -q "${version}"; then
      echo "[nix] Installing openclaw-dash ${version}..." >&2
      ${python}/bin/python -m venv "$VENV" 2>/dev/null || true
      "$VENV/bin/pip" install --quiet --upgrade \
        "git+https://github.com/dlorp/openclaw-dash.git@main" >&2
    fi

    exec "$VENV/bin/openclaw-dash" "$@"
  '';
in
{
  home.packages = [ openclawDash ];
}
