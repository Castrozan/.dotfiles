{ pkgs, config, ... }:
{
  home.activation.removeMcporterInstallation = config.lib.dag.entryAfter [ "linkGeneration" ] ''
    mcporterExecutable="${config.home.homeDirectory}/.local/share/mcporter-npm/lib/node_modules/mcporter/dist/cli.js"
    if [ -f "$mcporterExecutable" ]; then
      run ${pkgs.coreutils}/bin/timeout 30 ${pkgs.nodejs_22}/bin/node "$mcporterExecutable" daemon stop || true
    fi
    run ${pkgs.coreutils}/bin/rm -rf -- \
      "${config.home.homeDirectory}/.local/share/mcporter-npm" \
      "${config.home.homeDirectory}/.mcporter"
  '';
}
