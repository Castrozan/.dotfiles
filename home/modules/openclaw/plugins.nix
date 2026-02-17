# OpenClaw plugin management — install tracking and config patches.
#
# Plugins are installed via `openclaw plugins install` (npm registry).
# This module pins their config in openclaw.json so rebuilds don't lose it.
# Add new plugins: declare in openclaw.plugins option, add config patches below.
{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;
  nodePath = "${pkgs.nodejs_22}/bin";
  chromePath = "${pkgs.chromium}/bin/chromium";

  mcpAdapterInstallPath = "${homeDir}/.openclaw/extensions/openclaw-mcp-adapter";

  mcpServers = [
    {
      name = "chrome-devtools";
      transport = "stdio";
      command = "${nodePath}/npx";
      args = [
        "chrome-devtools-mcp@latest"
        "--headless"
        "--executablePath"
        chromePath
        "--usageStatistics"
        "false"
      ];
      env = {
        PATH = "${nodePath}:/usr/bin:/bin";
      };
    }
  ];
in
{
  config = {
    openclaw.configPatches = lib.mkOptionDefault {
      ".plugins.allow" = [
        "openclaw-mcp-adapter"
        "telegram"
        "memory-core"
        "device-pair"
        "phone-control"
        "talk-voice"
      ];
      ".plugins.entries.openclaw-mcp-adapter.enabled" = true;
      ".plugins.entries.openclaw-mcp-adapter.config" = {
        servers = mcpServers;
        toolPrefix = true;
      };
      ".plugins.installs.openclaw-mcp-adapter" = {
        source = "npm";
        spec = "openclaw-mcp-adapter";
        installPath = mcpAdapterInstallPath;
        version = "0.1.1";
      };
    };
  };
}
