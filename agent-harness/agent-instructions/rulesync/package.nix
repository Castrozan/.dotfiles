{ pkgs }:
let
  nodeModules = pkgs.importNpmLock.buildNodeModules {
    npmRoot = ./runtime;
    nodejs = pkgs.nodejs_22;
  };
in
pkgs.writeShellScriptBin "rulesync" ''
  exec ${pkgs.nodejs_22}/bin/node ${nodeModules}/node_modules/rulesync/dist/cli/index.js "$@"
''
