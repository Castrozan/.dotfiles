# Agent Grid Configuration
# This file defines agent metadata for the OpenClaw multi-agent system.
# Network identifiers (host:port) are stored in agenix at /run/agenix/grid-hosts.
#
# To add a new agent:
# 1. Add an entry to the agents attribute set below
# 2. Add host:port to the grid-hosts agenix secret
# 3. Create a token file at ~/.openclaw/grid-tokens/<agent-name>.token
# 4. Run nixos-rebuild to deploy the updated grid config to all agents
{
  agents = {
    clever = {
      emoji = "🤖";
      role = "home/personal - NixOS, home automation, overnight work";
      workspace = "~/openclaw";
    };
    robson = {
      emoji = "⚽";
      role = "work - Betha, code, productivity";
      workspace = "~/openclaw";
    };
  };
}
