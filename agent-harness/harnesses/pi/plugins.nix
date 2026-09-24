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
    ".pi/agent/plugins/dotfiles".source = "${config.agentPlugins.bundle}/plugin";
    ".pi/agent/extensions/agent-plugins".source = "${loaders}/node_modules/pi-agent-plugins";
    ".pi/agent/extensions/mcp-adapter".source = "${loaders}/node_modules/pi-mcp-adapter";
  };
  home.activation.registerProductionPiPlugin = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    PI_AGENT_DIR="${config.home.homeDirectory}/.pi/agent" \
    PI_CODING_AGENT_DIR="${config.home.homeDirectory}/.pi/agent" \
    ${pkgs.nodejs_22}/bin/node ${./scripts/register-managed-plugin.mjs} \
      ${loaders}/node_modules \
      ${config.agentPlugins.bundle}/plugin
  '';
}
