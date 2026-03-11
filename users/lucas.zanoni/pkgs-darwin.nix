{ pkgs, ... }:
{
  home.packages = with pkgs; [
    bat
    curl
    delta
    eza
    fd
    fzf
    gh
    git
    jq
    lazygit
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
