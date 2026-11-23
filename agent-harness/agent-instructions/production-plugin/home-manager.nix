{
  pkgs,
  lib,
  hostname,
  inputs,
  isDarwin,
  config,
  latest,
  ...
}:
let
  distribution = import ../../plugin-distribution { inherit pkgs; };
  desktopComputerUse = import ../skills/workstation/desktop/install { inherit pkgs; };
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
    avatarPlugin = lib.mkOption {
      type = lib.types.path;
      default = inputs.avatar.outPath;
      readOnly = true;
      description = "Avatar agent plugin: the avatar flake source at the pinned revision that also supplies its runtime.";
    };
  };

  config.home = {
    inherit (desktopComputerUse) packages;
    file = {
      ".local/share/agent-plugins/dotfiles".source = config.agentPlugins.bundle;
      ".local/share/agent-plugins/avatar".source = config.agentPlugins.avatarPlugin;
    };
  };
}
