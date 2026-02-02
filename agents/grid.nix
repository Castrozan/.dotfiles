# Agent Grid Configuration
# This file defines all agents in the OpenClaw multi-agent system.
# Agents communicate via HTTP API over Tailscale.
#
# To add a new agent:
# 1. Add an entry to the agents attribute set below
# 2. Create a token file at ~/.openclaw/grid-tokens/<agent-name>.token
# 3. Run nixos-rebuild to deploy the updated grid.md to all agents
{
  agents = {
    cleber = {
      emoji = "🤖";
      host = "REDACTED_IP_1";
      port = 18789;
      role = "home/personal - NixOS, home automation, overnight work";
      workspace = "~/openclaw";
    };
    romario = {
      emoji = "⚽";
      host = "REDACTED_IP_2";
      port = 18790;
      role = "work - Betha, code, productivity";
      workspace = "~/romario";
    };
  };
}
