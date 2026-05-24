{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  mcporterNpmPrefix = "$HOME/.local/share/mcporter-npm";
  mcporterServerConfig = {
    mcpServers = { };
  };

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
