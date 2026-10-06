{
  profileDirectory,
  defaultMode ? "build",
}:
{
  pkgs,
  config,
  lib,
  ...
}:
let
  loaders = import ./plugin-loaders { inherit pkgs; };
  loopGuard = import ./plugin-loaders/loop-guard.nix { inherit pkgs loaders; };
in
{
  imports = [ ../../agent-instructions/production-plugin/home-manager.nix ];

  home.file = {
    "${profileDirectory}/plugins/dotfiles".source = "${config.agentPlugins.bundle}/plugin";
    "${profileDirectory}/extensions/agent-plugins".source = "${loaders}/node_modules/pi-agent-plugins";
    "${profileDirectory}/extensions/mcp-adapter".source = "${loaders}/node_modules/pi-mcp-adapter";
    "${profileDirectory}/extensions/agent-modes".source = "${loaders}/node_modules/pi-agent-modes";
    "${profileDirectory}/extensions/loop-guard".source = loopGuard;
    "${profileDirectory}/modes.config.json".text = builtins.toJSON {
      inherit defaultMode;
      modes = {
        ask = {
          instructions = ''
            Answer from the conversation. Chat mode blocks file, shell, and MCP tools.
            For repository inspection, use /mode plan or /mode review; for changes, use /mode build.
          '';
          bash = "deny";
          blockTools = [
            "read"
            "grep"
            "find"
            "ls"
          ];
          thinkingLevel = null;
        };
        plan.thinkingLevel = null;
        review.thinkingLevel = null;
        debug.thinkingLevel = null;
      };
    };
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
