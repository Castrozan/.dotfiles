{ ... }:
{
  imports = [
    ./claude.nix
    ./config.nix
    ./agents.nix
    ./skills.nix
    ./hooks.nix
    ./lsp.nix # LSP binaries for Claude Code
    ./mcp.nix
    ./private.nix # Private/sensitive configs from ~/.private-config/claude/
    ./stt.nix # Build dependencies for claude-stt plugin
  ];
}
