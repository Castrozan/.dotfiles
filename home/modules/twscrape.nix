{ pkgs, ... }:
let
  python = pkgs.python312;
  twikitVersion = "2.3.3";
  virtualenvPath = "$HOME/.local/share/twikit-venv";
  secretsDirectory = "$HOME/.secrets";
  cookiesPath = "$HOME/.config/twikit/cookies.json";

  twikitCliSource = pkgs.writeText "twikit-cli.py" (
    builtins.readFile ../../agents/skills/twscrape/scripts/twikit-cli.py
  );

  extractXCookiesSource = pkgs.writeText "extract-x-cookies.py" (
    builtins.readFile ../../agents/skills/twscrape/scripts/extract-x-cookies.py
  );

  twikitCli = pkgs.writeShellScriptBin "twikit-cli" ''
    set -euo pipefail

    VENV="${virtualenvPath}"

    if [ ! -f "$VENV/bin/python" ] || ! "$VENV/bin/pip" show twikit 2>/dev/null | grep -q "${twikitVersion}"; then
      echo "[nix] Installing twikit ${twikitVersion}..." >&2
      ${python}/bin/python -m venv "$VENV" 2>/dev/null || true
      "$VENV/bin/pip" install --quiet --upgrade "twikit==${twikitVersion}" >&2
    fi

    export TWIKIT_COOKIES_PATH="${cookiesPath}"
    export TWIKIT_USERNAME_FILE="${secretsDirectory}/x-username"
    export TWIKIT_EMAIL_FILE="${secretsDirectory}/x-email"
    export TWIKIT_PASSWORD_FILE="${secretsDirectory}/x-password"

    # Special command: extract cookies from browser
    if [ "''${1:-}" = "extract-cookies" ]; then
      exec ${python}/bin/python "${extractXCookiesSource}"
    fi

    exec "$VENV/bin/python" "${twikitCliSource}" "$@"
  '';
in
{
  home.packages = [ twikitCli ];
}
