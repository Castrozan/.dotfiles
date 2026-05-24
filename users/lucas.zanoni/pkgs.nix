{
  # Dependency injection
  pkgs,
  lib,
  latest,
  ...
}:
{
  home.packages =
    with pkgs;
    [
      awscli2
      alejandra
      bash-completion
      bat
      bats
      brave
      bun
      cargo
      curl
      delta
      docker-compose
      duckdb
      dust
      eza
      fastfetch
      fd
      fzf
      gdrive3
      gh
      glab
      # ghostty TODO: fix ghostty, https://gitlab.gnome.org/GNOME/gtk/-/issues/4950. A wrapper did not work.
      git
      gnutar
      go

      insomnia
      jq
      kubectl
      # lens TODO: fix lens, im using the snap version for now
      micronaut
      mongosh
      neofetch
      # nix # leave the manually installed version
      nixd
      nixfmt-rfc-style
      nodejs
      nodePackages.prettier
      obsidian
      ollama
      pipes
      postman
      postgresql
      ripgrep-all
      ruff
      rustc
      shellcheck
      shfmt
      tailscale
      tealdeer
      tree
      unzip
      uv
      vim
      whisper-cpp
      yamllint
      zip
      zoxide
    ]
    ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux (
      with pkgs;
      [
        cava
        gnome-shell-extensions
        gnome-extension-manager
        gnomeExtensions.default-workspace
        gnomeExtensions.workspace-matrix
        imv
        i2p
        i2pd
        i2pd-tools
        playerctl
        pavucontrol
        pulsemixer
        quickemu
        redisinsight
        wiremix
        wl-clipboard
        wtype
        xclip
        ydotool
      ]
    )
    # Appending to list
    ++ (with latest; [
      lazydocker
      # gemini-cli TODO: fix gemini-cli, im using the npm version for now
      suwayomi-server
    ]);
}
