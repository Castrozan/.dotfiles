{ pkgs, ... }:
let
  version = "1.0.11";
  crabwalkHome = "$HOME/.crabwalk";

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

    exec "$HOME/.local/bin/crabwalk-bin" "$@"
  '';
in
{
  home.packages = [ crabwalkInstaller ];
}
