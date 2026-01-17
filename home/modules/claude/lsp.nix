# LSP binaries for Claude Code
# NOTE: Claude Code's plugin system expects git-based marketplaces,
# so custom local marketplaces don't work. These LSP servers are
# installed directly and available in PATH for tools that support them.
{ pkgs, ... }:
{
  home.packages = with pkgs; [
    # TypeScript/JavaScript
    typescript-language-server
    typescript

    # Java
    jdt-language-server

    # Nix
    nixd
    nixfmt-rfc-style

    # Bash/shell
    bash-language-server
  ];
}
