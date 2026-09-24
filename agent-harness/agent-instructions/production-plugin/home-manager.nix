{
  pkgs,
  lib,
  hostname,
  config,
  latest,
  ...
}:
let
  distribution = import ../../plugin-distribution { inherit pkgs; };
  source = import ./. {
    inherit pkgs lib hostname;
    inherit (config.home) homeDirectory;
    chromePackage = latest.google-chrome;
  };
in
{
  options.agentPlugins.bundle = lib.mkOption {
    type = lib.types.package;
    default = distribution.buildPlugin { inherit source; };
    readOnly = true;
    description = "Complete production plugin and native discovery projections.";
  };

  config.home.file.".local/share/agent-plugins/dotfiles".source = config.agentPlugins.bundle;
}
