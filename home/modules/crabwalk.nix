{ pkgs, ... }:
let
  version = "1.0.11";
  crabwalkHome = "$HOME/.crabwalk";
  gatewayConfigPath = "$HOME/.openclaw/openclaw.json";

  crabwalkInstaller = pkgs.writeShellScriptBin "crabwalk" ''
    set -euo pipefail

    CRABWALK_HOME="${crabwalkHome}"
    INSTALLED_VERSION=""
    if [ -f "$CRABWALK_HOME/version" ]; then
      INSTALLED_VERSION=$(cat "$CRABWALK_HOME/version" 2>/dev/null || echo "")
    fi

    if [ "$INSTALLED_VERSION" != "${version}" ]; then
      echo "[nix] Installing Crabwalk ${version}..." >&2
      mkdir -p "$CRABWALK_HOME" "$HOME/.local/bin"
      ${pkgs.curl}/bin/curl -sL \
        "https://github.com/luccast/crabwalk/releases/download/v${version}/crabwalk-v${version}.tar.gz" \
        | ${pkgs.gnutar}/bin/tar -xz -C "$CRABWALK_HOME"
      cp "$CRABWALK_HOME/bin/crabwalk" "$HOME/.local/bin/crabwalk-bin"
      chmod +x "$HOME/.local/bin/crabwalk-bin"

      ${pkgs.gnused}/bin/sed -i \
        's|nohup node |nohup ${pkgs.nodejs_22}/bin/node |g' \
        "$HOME/.local/bin/crabwalk-bin"
      ${pkgs.gnused}/bin/sed -i \
        's|exec node |exec ${pkgs.nodejs_22}/bin/node |g' \
        "$HOME/.local/bin/crabwalk-bin"

      echo "${version}" > "$CRABWALK_HOME/version"
    fi

    GATEWAY_TOKEN=""
    GATEWAY_PORT="18790"
    if [ -f "${gatewayConfigPath}" ]; then
      GATEWAY_TOKEN=$(${pkgs.jq}/bin/jq -r '.gateway.token // empty' "${gatewayConfigPath}" 2>/dev/null || echo "")
      GATEWAY_PORT=$(${pkgs.jq}/bin/jq -r '.gateway.port // 18790' "${gatewayConfigPath}" 2>/dev/null || echo "18790")
    fi

    # Pass gateway args only for start command (not --version, --help, stop, status)
    FIRST_ARG="''${1:-start}"
    if [ "$FIRST_ARG" = "start" ] || [ "$FIRST_ARG" = "-d" ] || [ "$FIRST_ARG" = "--daemon" ]; then
      EXTRA_ARGS=""
      if [ -n "$GATEWAY_TOKEN" ]; then
        EXTRA_ARGS="$EXTRA_ARGS -t $GATEWAY_TOKEN"
      fi
      EXTRA_ARGS="$EXTRA_ARGS -g ws://127.0.0.1:$GATEWAY_PORT"
      exec "$HOME/.local/bin/crabwalk-bin" $EXTRA_ARGS "$@"
    else
      exec "$HOME/.local/bin/crabwalk-bin" "$@"
    fi
  '';
in
{
  home.packages = [ crabwalkInstaller ];
}
