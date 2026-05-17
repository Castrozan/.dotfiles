{ config, pkgs, ... }:
let
  lspServersAndTooling = with pkgs; [
    lua-language-server
    stylua

    pyright
    ruff

    nixd
    nixfmt-rfc-style
    statix
    deadnix

    typescript-language-server
    nodePackages.prettier
    nodePackages.eslint

    rust-analyzer

    gopls
    go
    gotools

    bash-language-server

    marksman
    markdownlint-cli2

    terraform-ls

    jdt-language-server
    jdk21
    jdk17

    fd
    ripgrep
    tree-sitter
    gcc
  ];
in
{
  home.file.".config/nvim".source =
    config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/.config/nvim";

  programs.neovim = {
    enable = true;
    defaultEditor = true;
    viAlias = true;
    vimAlias = true;
  };

  home.packages = lspServersAndTooling;
}
