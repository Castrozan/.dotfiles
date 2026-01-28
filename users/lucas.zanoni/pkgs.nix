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
      bats
      brave
      bruno
      bun
      cargo
      clipse
      curl
      delta
      docker-compose
      fastfetch
      flameshot
      fzf
      gh
      git-crypt
      glab
      # ghostty TODO: fix ghostty, https://gitlab.gnome.org/GNOME/gtk/-/issues/4950. A wrapper did not work.
      git
      gnome-shell-extensions
      gnome-extension-manager
      gnomeExtensions.default-workspace
      gnomeExtensions.workspace-matrix
      gnutar
      go
      google-chrome
      insomnia
      (jetbrains.idea-ultimate.override { vmopts = "-Dawt.toolkit.name=WLToolkit"; })
      jq
      kubectl
      ksnip
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
      rustc
      tailscale
      tree
      unzip
      uv
      vim
      wl-clipboard
      wtype
      xclip
      yamllint
      zip
      zoxide
      zsh
    ]
    # Appending to list
    ++ (with latest; [
      lazydocker
      # gemini-cli TODO: fix gemini-cli, im using the npm version for now
      suwayomi-server
    ]);
}
