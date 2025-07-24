{
  # Dependecy injection
  pkgs,
  latest,
  ...
}:
{
  home.packages = with pkgs; [
    cbonsai
    clipse
    flameshot
    fzf
    gh
    neofetch
    nix
    nodejs
    obsidian
    pipes
    vim
    yazi
    zoxide
    zsh
    bash-completion
    bat
    git
    xclip
    delta
    curl
    zip
    unzip
    gnutar
    curl
    lazydocker
    ripgrep-all
    latest.direnv
    latest.devenv
    tree

    # nix formatting tools
    nixd
    nixfmt-rfc-style
    alejandra

    brave
    insomnia
    uv
    postman
    redisinsight
    lens
    latest.vscode
    latest.code-cursor
    latest.claude-code
    latest.gemini-cli
  ];
}
