{
  repository,
  system ? "x86_64-linux",
}:
let
  dependencies = (builtins.getFlake repository).inputs.dependencies.inputs;
  channels = import "${repository}/repository/flake-assembly/channels.nix" {
    inputs = dependencies;
    inherit system;
  };
  inherit (channels) pkgs;
  source = import "${repository}/agent-harness/agent-instructions/production-plugin" {
    inherit pkgs;
    inherit (pkgs) lib;
    hostname = "ci";
    homeDirectory = "/var/empty/verdr-ci";
    chromePackage = pkgs.google-chrome;
    isDarwin = false;
  };
in
(import "${repository}/agent-harness/plugin-distribution" { inherit pkgs; }).buildPlugin {
  inherit source;
  opencodeDataRoot = "/var/empty/verdr-ci/state/agent-plugins/opencode";
}
