{
  pkgs,
  lib,
  homeDirectory,
  chromePackage,
}:
let
  servers = import ./mcp-servers.nix { inherit pkgs homeDirectory chromePackage; };
  launchers = lib.mapAttrsToList (name: server: {
    name = "native/mcp/${name}";
    path = pkgs.writeShellScript "dotfiles-mcp-${name}" ''
      exec ${lib.escapeShellArg server.command} "$@"
    '';
  }) servers;
  portableServers = lib.mapAttrs (
    name: server:
    server
    // {
      command = "./native/mcp/${name}";
    }
  ) servers;
  claudeServers = lib.mapAttrs (
    name: server:
    server
    // {
      command = "\${CLAUDE_PLUGIN_ROOT}/native/mcp/${name}";
    }
  ) servers;
in
launchers
++ [
  {
    name = "mcp.json";
    path = pkgs.writeText "dotfiles-mcp.json" (
      builtins.toJSON {
        "$schema" = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json";
        mcpServers = portableServers;
      }
    );
  }
  {
    name = ".claude-plugin/mcp.json";
    path = pkgs.writeText "dotfiles-claude-mcp.json" (builtins.toJSON { mcpServers = claudeServers; });
  }
]
