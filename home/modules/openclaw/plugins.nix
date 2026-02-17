# OpenClaw plugin management — install tracking and config patches.
#
# Plugins are installed via `openclaw plugins install` (npm registry).
# This module pins their config in openclaw.json so rebuilds don't lose it.
# Add new plugins: declare in openclaw.plugins option, add config patches below.
#
# MCP tools: use mcporter (see home/modules/mcporter.nix), NOT openclaw-mcp-adapter.
# The adapter plugin only injects tools into the default agent's session due to
# a gateway architecture constraint (androidStern/openclaw-mcp-adapter#6).
# mcporter uses file-based SKILL.md registration which works for ALL agents.
{ lib, ... }:
{
  config = {
    openclaw.configPatches = lib.mkOptionDefault {
      ".plugins.allow" = [
        "telegram"
        "memory-core"
        "device-pair"
        "phone-control"
        "talk-voice"
      ];
    };
  };
}
