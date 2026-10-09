{ pkgs }:
pkgs.importNpmLock.buildNodeModules {
  npmRoot = ./.;
  nodejs = pkgs.nodejs_22;
  derivationArgs = {
    doInstallCheck = true;
    installCheckPhase = ''
      test -f "$out/node_modules/@earendil-works/pi-coding-agent/dist/index.js"
      test -f "$out/node_modules/pi-agent-plugins/extensions/index.ts"
      test -f "$out/node_modules/pi-mcp-adapter/index.ts"
      node "$out/node_modules/@earendil-works/pi-coding-agent/dist/cli.js" --version
      node ${./check-loaders.mjs} "$out/node_modules"
    '';
  };
}
