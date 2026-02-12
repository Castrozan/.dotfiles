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
      curl
      delta
      docker-compose
      dust
      eza
      fastfetch
      fd
      flameshot
      fzf
      gh
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
      jetbrains.idea
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
      playerctl
      pipes
      postman
      postgresql
      redisinsight
      ripgrep-all
      rustc
      tailscale
      tealdeer
      tree
      unzip
      uv
      vim
      whisper-cpp
      wiremix
      wl-clipboard
      wtype
      xclip
      yamllint
      zip
      zoxide
    ]
    # Appending to list
    ++ (with latest; [
      lazydocker
      # gemini-cli TODO: fix gemini-cli, im using the npm version for now
      suwayomi-server
    ]);
}
