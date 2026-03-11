{ pkgs, ... }:
{
  home.packages = with pkgs; [
    bat
    brave
    curl
    delta
    eza
    fd
    fzf
    gh
    git
    jq
    nixd
    nixfmt-rfc-style
    nodejs
    ripgrep-all
    shellcheck
    shfmt
    tealdeer
    tree
    unzip
    vim
    zip
    zoxide
  ];
}
