{
  pkgs,
  unstable,
  latest,
  ...
}:
{
  # List of pkgs installed from nixpkgs. To search, run: nix search wget
  environment.systemPackages =
    with pkgs;
    [
      alejandra
      ani-cli
      awscli2
      bash
      bash-completion
      bats
      bun
      btop
      cacert
      curl
      dbeaver-bin
      deno
      (discord.override {
        withOpenASAR = true;
        withVencord = true; # For customization
      })
      docker
      dust
      eza
      fastfetch
      fd
      ffmpeg

      fzf
      gh
      git
      chromium
      google-chrome
      gnumake
      htop
      imv
      jq
      just
      k6
      ksnip
      lazydocker
      lshw
      mpv
      mpv-handler
      mpvc
      mpv-shim-default-shaders
      nixd
      nix-prefetch-github
      nixpkgs-fmt
      nodejs
      nodePackages.prettier
      obs-studio
      obsidian
      pavucontrol
      p7zip
      pipes
      playerctl
      pnpm
      poetry
      postman
      pulsemixer
      python312
      scrcpy
      shellcheck
      shfmt
      sqlite
      tig # git log visualizer
      tealdeer
      tmux
      tree
      unzip
      usbutils
      vesktop
      vim
      vlc
      wget
      whisper-cpp
      wgnord # Note: Should install manually from github.com/phirecc/wgnord
      wiremix
      wireguard-go
      wireguard-tools
      wl-clipboard
      xclip
      yazi
      yarn
      zip
      zoxide
    ]
    # Unstable packages
    ++ (with unstable; [
      brave
      cargo
      gcc
      rustc
      rustPlatform.rustcSrc
      openssl.dev
      openssl
      SDL2
      alsa-lib.dev
      pkg-config
      supabase-cli
      terraform # Removed: its broken on nixpkgs
    ])
    # Latest packages
    ++ (with latest; [
      gemini-cli
      vscode
    ]);
}
