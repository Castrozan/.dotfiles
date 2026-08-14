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

  # jdtls itself runs on jdk21, but a project that pins source and target to 1.8 has to be
  # compiled against a real java 8 runtime or jdt reads it with java 21 rules: java.lang.Record
  # collides with the project's own Record, and javax.annotation.Resource, dropped from the jdk
  # in 11, stops resolving. Neither is a fault in the code being edited.
  javaEightHome = "${pkgs.jdk8.home}";

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
    viAlias = true;
    vimAlias = true;
    # on the wrapper rather than in home.sessionVariables: panes inherit the environment of the
    # terminal server they were spawned from, which outlives a rebuild, so a session variable
    # reaches neovim only after that server restarts
    extraWrapperArgs = [
      "--set"
      "JAVA_8_HOME"
      javaEightHome
    ];
  };

  home.packages = lspServersAndTooling;
}
