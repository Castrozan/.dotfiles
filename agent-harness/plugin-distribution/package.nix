{ pkgs }:
let
  nodeModules = pkgs.importNpmLock.buildNodeModules {
    npmRoot = ./runtime;
    nodejs = pkgs.nodejs_22;
  };
  dotagents = pkgs.writeShellScript "dotagents-plugin-builder" ''
    exec ${pkgs.nodejs_22}/bin/node ${nodeModules}/node_modules/@sentry/dotagents/dist/cli/index.js "$@"
  '';
in
pkgs.writeShellApplication {
  name = "agent-plugin-build";
  runtimeInputs = [ pkgs.python312 ];
  text = ''
    export DOTAGENTS_PLUGIN_BUILDER=${dotagents}
    exec python3 ${./scripts}/build_plugin.py "$@"
  '';
}
