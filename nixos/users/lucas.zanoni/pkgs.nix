{
  pkgs,
  latest,
  ...
}:
{

  imports = [
    ../../home/modules/dooit.nix
    ../../home/modules/pipx.nix
    ../../home/modules/sdkman.nix
  ];

  home.packages = with pkgs; [
    git
    xclip
    curl
    zip
    unzip
    gnutar
    curl
    lazydocker
    ripgrep-all
    latest.direnv
    latest.devenv

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
