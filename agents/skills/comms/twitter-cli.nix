{
  pkgs,
  homeDir,
}:
let
  python = pkgs.python312;
  twikitVersion = "2.3.3";
  twikitVirtualenvPath = "${homeDir}/.local/share/twikit-venv";
  secretsDirectory = "${homeDir}/.secrets";
  twikitCookiesPath = "${homeDir}/.config/twikit/cookies.json";

  twikitCliSource = pkgs.writeText "twikit-cli.py" (builtins.readFile ./scripts/twikit-cli.py);

  extractXCookiesSource = pkgs.writeText "extract-x-cookies.py" (
    builtins.readFile ./scripts/extract-x-cookies.py
  );

  patchTwikitTransactionSource = pkgs.writeText "patch-twikit-transaction.py" (
    builtins.readFile ./scripts/patch-twikit-transaction.py
  );

  twikitCli = pkgs.writeShellScriptBin "twikit-cli" ''
    set -euo pipefail

    VENV="${twikitVirtualenvPath}"

    INSTALLED_TWIKIT_VERSION=$("$VENV/bin/pip" show twikit 2>/dev/null | grep -oP 'Version: \K.*' || echo "none")
    if [ ! -f "$VENV/bin/python" ] || [ "$INSTALLED_TWIKIT_VERSION" != "${twikitVersion}" ]; then
      echo "[nix] Installing twikit ${twikitVersion}..." >&2
      ${python}/bin/python -m venv "$VENV" 2>/dev/null || true
      "$VENV/bin/pip" install --quiet --upgrade "twikit==${twikitVersion}" pycryptodome secretstorage >&2
      TWIKIT_CLIENT="$VENV/lib/python3.12/site-packages/twikit/client/client.py"
      if [ -f "$TWIKIT_CLIENT" ]; then
        ${pkgs.gnused}/bin/sed -i "s/\['itemContent'\]\['value'\]/['value']/g" "$TWIKIT_CLIENT"
      fi
      ${python}/bin/python "${patchTwikitTransactionSource}" "$VENV"
    fi

    export TWIKIT_COOKIES_PATH="${twikitCookiesPath}"

    if [ ! -f "${twikitCookiesPath}" ] && [ -f "${secretsDirectory}/x-cookies" ]; then
      mkdir -p "$(dirname "${twikitCookiesPath}")"
      cp "${secretsDirectory}/x-cookies" "${twikitCookiesPath}"
      chmod 600 "${twikitCookiesPath}"
      echo "[nix] Seeded cookies from agenix secret" >&2
    fi
    export TWIKIT_USERNAME_FILE="${secretsDirectory}/x-username"
    export TWIKIT_EMAIL_FILE="${secretsDirectory}/x-email"
    export TWIKIT_PASSWORD_FILE="${secretsDirectory}/x-password"

    if [ "''${1:-}" = "extract-cookies" ]; then
      exec "$VENV/bin/python" "${extractXCookiesSource}"
    fi

    exec "$VENV/bin/python" "${twikitCliSource}" "$@"
  '';
in
{
  packages = [ twikitCli ];
}
