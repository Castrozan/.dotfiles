{ pkgs, ... }:
let
  python = pkgs.python312;
  twikitVersion = "2.3.3";
  twikitVirtualenvPath = "$HOME/.local/share/twikit-venv";
  secretsDirectory = "$HOME/.secrets";
  twikitCookiesPath = "$HOME/.config/twikit/cookies.json";

  twikitCliSource = pkgs.writeText "twikit-cli.py" (
    builtins.readFile ../../agents/skills/twitter/scripts/twikit-cli.py
  );

  extractXCookiesSource = pkgs.writeText "extract-x-cookies.py" (
    builtins.readFile ../../agents/skills/twitter/scripts/extract-x-cookies.py
  );

  twikitCli = pkgs.writeShellScriptBin "twikit-cli" ''
    set -euo pipefail

    VENV="${twikitVirtualenvPath}"

    INSTALLED_TWIKIT_VERSION=$("$VENV/bin/pip" show twikit 2>/dev/null | grep -oP 'Version: \K.*' || echo "none")
    if [ ! -f "$VENV/bin/python" ] || [ "$INSTALLED_TWIKIT_VERSION" != "${twikitVersion}" ]; then
      echo "[nix] Installing twikit ${twikitVersion}..." >&2
      ${python}/bin/python -m venv "$VENV" 2>/dev/null || true
      "$VENV/bin/pip" install --quiet --upgrade "twikit==${twikitVersion}" >&2
    fi

    export TWIKIT_COOKIES_PATH="${twikitCookiesPath}"
    export TWIKIT_USERNAME_FILE="${secretsDirectory}/x-username"
    export TWIKIT_EMAIL_FILE="${secretsDirectory}/x-email"
    export TWIKIT_PASSWORD_FILE="${secretsDirectory}/x-password"

    if [ "''${1:-}" = "extract-cookies" ]; then
      exec ${python}/bin/python "${extractXCookiesSource}"
    fi

    exec "$VENV/bin/python" "${twikitCliSource}" "$@"
  '';

  grokSearchSource = builtins.readFile ../../agents/skills/twitter/scripts/grok-search.sh;

  grokSearchCli = pkgs.writeShellScriptBin "grok-search" grokSearchSource;
in
{
  home.packages = [
    twikitCli
    grokSearchCli
  ];
}
