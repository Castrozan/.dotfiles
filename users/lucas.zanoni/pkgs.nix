{
  # Dependency injection
  pkgs,
  latest,
  ...
}:
{
  home.packages =
    with pkgs;
    [
      alejandra
      bash-completion
      bat
      brave
      bruno
      clipse
      curl
      delta
      discord
      docker-compose
      fastfetch
      flameshot
      fzf
      gh
      ghostty
      git
      gnutar
      go
      insomnia
      jq
      kubectl
      # lens TODO: fix lens, im using the snap version for now
      micronaut
      neofetch
      # nix # leave the manually installed version
      nixd
      nixfmt-rfc-style
      nodejs
      obsidian
      ollama
      pipes
      postman
      redisinsight
      ripgrep-all
      tree
      unzip
      uv
      vim
      wl-clipboard
      xclip
      yamllint
      yazi
      zip
      zoxide
      zsh
    ]
    # Appending to list
    ++ (with latest; [
      claude-code
      devenv
      lazydocker
      # gemini-cli TODO: fix gemini-cli, im using the npm version for now
    ]);
}
