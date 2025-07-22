{
  # Dependecy injection
  pkgs,
  latest,
  ...
}:
{
  home.packages = with pkgs; [
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
    latest.code-cursor
    latest.claude-code
    latest.gemini-cli
  ];
}
