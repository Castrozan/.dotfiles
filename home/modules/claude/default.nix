{ ... }:
{
  imports = [
    ./claude.nix
    ./config.nix
    ./agents.nix
    ./skills.nix
    ./mcp.nix
    ./private.nix # Private/sensitive configs from ~/.private-config/claude/
    ./stt.nix # Build dependencies for claude-stt plugin
  ];
}
