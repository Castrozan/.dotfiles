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
    prettier
    eslint
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

  javaEightHome = "${pkgs.jdk8.home}";

  pdfViewerTooling = with pkgs; [
    imagemagick
    ghostscript
    poppler-utils
  ];

  brazilianPortugueseSpellFile = pkgs.fetchurl {
    url = "https://ftp.nluug.nl/pub/vim/runtime/spell/pt.utf-8.spl";
    hash = "sha256-Pl/BALaVG3g8+zOGraQ8s5g5VT4E+qQVr1z1vV1qtjs=";
  };
in
{
  home.file.".config/nvim".source =
    config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/machine-configuration/editors/neovim/program-configuration";

  xdg.dataFile."nvim/site/spell/pt.utf-8.spl".source = brazilianPortugueseSpellFile;

  programs.neovim = {
    enable = true;
    extraPackages = pdfViewerTooling;
    viAlias = true;
    vimAlias = true;
    withPython3 = true;
    withRuby = true;
    sideloadInitLua = true;
    extraWrapperArgs = [
      "--set"
      "JAVA_8_HOME"
      javaEightHome
    ];
  };

  home.packages = lspServersAndTooling;
}
