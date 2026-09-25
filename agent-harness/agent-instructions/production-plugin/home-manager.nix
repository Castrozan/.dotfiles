{
  pkgs,
  lib,
  hostname,
  isDarwin,
  config,
  latest,
  ...
}:
let
  distribution = import ../../plugin-distribution { inherit pkgs; };
  source = import ./. {
    inherit
      pkgs
      lib
      hostname
      isDarwin
      ;
    inherit (config.home) homeDirectory;
    chromePackage = latest.google-chrome;
  };
in
{
  options.agentPlugins = {
    opencodeDataRoot = lib.mkOption {
      type = lib.types.str;
      default = "${config.xdg.stateHome}/agent-plugins/opencode";
      readOnly = true;
      description = "Deployment-owned persistent state for native OpenCode plugin processes.";
    };
    bundle = lib.mkOption {
      type = lib.types.package;
      default = distribution.buildPlugin {
        inherit source;
        inherit (config.agentPlugins) opencodeDataRoot;
      };
      readOnly = true;
      description = "Complete production plugin and native discovery projections.";
    };
  };

  config.home.file.".local/share/agent-plugins/dotfiles".source = config.agentPlugins.bundle;
}
