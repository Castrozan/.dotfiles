{ ... }:
{
  imports = [
    ./claude.nix
    ./config.nix
    ./agents.nix
    ./skills.nix
    ./hooks.nix
    ./lsp.nix
    ./mcp.nix
    ./private.nix
    # TODO: these both waste too much usage of claude code subscription
    # ./session-rename.nix # Automatic session naming service
    # ./rename-session.nix
  ];
}
