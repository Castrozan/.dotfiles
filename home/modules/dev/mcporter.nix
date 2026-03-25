{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  mcporterNpmPrefix = "$HOME/.local/share/mcporter-npm";
  scraplingMcp = pkgs.writeShellScript "scrapling-mcp" ''
    export PLAYWRIGHT_BROWSERS_PATH="$HOME/.local/share/scrapling-browsers"
    exec "$HOME/.local/share/scrapling-venv/bin/python" -m scrapling_fetch_mcp.mcp "$@"
  '';

  mcporterServerConfig = {
    mcpServers = {
      scrapling-fetch = {
        command = "${scraplingMcp}";
        args = [ ];
      };
    };
  };

  scraplingVenvPath = "$HOME/.local/share/scrapling-venv";

  installScraplingFetchMcpVenv = pkgs.writeShellScript "scrapling-fetch-mcp-venv-install" ''
    set -euo pipefail
    VENV="${scraplingVenvPath}"
    MARKER="$VENV/.installed-version"
    DESIRED_VERSION="0.2.0"

    if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "$DESIRED_VERSION" ]; then
      exit 0
    fi

    ${pkgs.python312}/bin/python3 -m venv "$VENV" --clear
    "$VENV/bin/pip" install --quiet "scrapling-fetch-mcp==$DESIRED_VERSION"
    echo "$DESIRED_VERSION" > "$MARKER"
  '';

  mcporterWrapper = pkgs.writeShellScriptBin "mcporter" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    exec "${mcporterNpmPrefix}/lib/node_modules/mcporter/dist/cli.js" "$@"
  '';

  installMcporterViaNpm = pkgs.writeShellScript "mcporter-install" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${mcporterNpmPrefix}"
    BIN="${mcporterNpmPrefix}/bin/mcporter"

    if [ -x "$BIN" ]; then
      exit 0
    fi

    ${nodejs}/bin/npm install -g "mcporter@latest" \
      --prefix "${mcporterNpmPrefix}" --no-audit --no-fund --loglevel=error
  '';

  restartMcporterDaemon = pkgs.writeShellScript "mcporter-daemon-restart" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    ${nodejs}/bin/node "${mcporterNpmPrefix}/lib/node_modules/mcporter/dist/cli.js" daemon restart || true
  '';
in
{
  home = {
    packages = [
      nodejs
      mcporterWrapper
    ];

    file.".mcporter/mcporter.json".text = builtins.toJSON mcporterServerConfig;

    activation = {
      installScraplingFetchMcpVenv = config.lib.dag.entryAfter [ "writeBoundary" ] ''
        run ${installScraplingFetchMcpVenv}
      '';

      installMcporterViaNpm = config.lib.dag.entryAfter [ "writeBoundary" ] ''
        run ${installMcporterViaNpm}
      '';

      restartMcporterDaemonAfterConfigChanges =
        config.lib.dag.entryAfter [ "installMcporterViaNpm" "linkGeneration" ]
          ''
            run ${restartMcporterDaemon}
          '';
    };
  };
}
