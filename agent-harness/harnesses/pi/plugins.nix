{ profileDirectory }:
{
  pkgs,
  config,
  lib,
  ...
}:
let
  loaders = import ./plugin-loaders { inherit pkgs; };
in
{
  imports = [ ../../agent-instructions/production-plugin/home-manager.nix ];

  home.file = {
    "${profileDirectory}/plugins/dotfiles".source = "${config.agentPlugins.bundle}/plugin";
    "${profileDirectory}/extensions/agent-plugins".source = "${loaders}/node_modules/pi-agent-plugins";
    "${profileDirectory}/extensions/mcp-adapter".source = "${loaders}/node_modules/pi-mcp-adapter";
  };
  home.activation."registerProductionPiPlugin-${profileDirectory}" =
    lib.hm.dag.entryAfter [ "linkGeneration" ]
      ''
        PI_AGENT_DIR=${lib.escapeShellArg "${config.home.homeDirectory}/${profileDirectory}"} \
        PI_CODING_AGENT_DIR=${lib.escapeShellArg "${config.home.homeDirectory}/${profileDirectory}"} \
        ${pkgs.nodejs_22}/bin/node ${./scripts/register-managed-plugin.mjs} \
          ${loaders}/node_modules \
          ${config.agentPlugins.bundle}/plugin
      '';
}
