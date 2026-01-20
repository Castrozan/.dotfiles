{...}: {
  imports = [
    ./claude.nix
    ./config.nix
    ./agents.nix
    ./skills.nix
    ./hook-symlinks.nix
    ./lsp.nix # LSP binaries for Claude Code
    ./mcp.nix
    ./private.nix # Private/sensitive configs from ~/.private-config/claude/
    ./session-rename.nix # Automatic session naming service
  ];
}
