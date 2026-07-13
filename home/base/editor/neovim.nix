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
    vscode-langservers-extracted

    rust-analyzer

    gopls
    go
    gotools

    bash-language-server

    marksman

    terraform-ls

    jdt-language-server
    jdk21

    fd
    ripgrep
    tree-sitter
    gcc
  ];

  brazilianPortugueseSpellFile = pkgs.fetchurl {
    url = "https://ftp.nluug.nl/pub/vim/runtime/spell/pt.utf-8.spl";
    hash = "sha256-Pl/BALaVG3g8+zOGraQ8s5g5VT4E+qQVr1z1vV1qtjs=";
  };
in
{
  home.file.".config/nvim".source =
    config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/.config/nvim";

  xdg.dataFile."nvim/site/spell/pt.utf-8.spl".source = brazilianPortugueseSpellFile;

  programs.neovim = {
    enable = true;
    viAlias = true;
    vimAlias = true;
  };

  home.packages = lspServersAndTooling;
}
