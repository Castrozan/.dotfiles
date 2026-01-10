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
      # Development Tools
      alejandra
      awscli2
      azure-cli
      dbeaver-bin
      cacert
      cypress
      docker
      gh
      git
      gnumake
      just
      k6
      lazydocker
      nixd
      nixpkgs-fmt
      nix-prefetch-github
      nodePackages.prettier
      # terraform # Removed: its broken on nixpkgs
      tig

      # Python and Dependencies
      python312
      python312Packages.fastapi
      python312Packages.httpx
      python312Packages.pip
      python312Packages.pydantic
      python312Packages.uv
      python312Packages.uvicorn
      poetry
      # TODO: migrate this to home-manager /home/packages/playwright.nix
      playwright-driver.browsers
      playwright-driver

      # System Utilities
      btop
      clipse
      ffmpeg
      fzf
      htop
      p7zip
      tmux
      unzip
      vim
      wl-clipboard
      wget
      xclip
      xsel # Required for tmux yank
      yazi
      zip
      zoxide
      zsh

      # Network Tools
      wgnord # Note: Should install manually from github.com/phirecc/wgnord
      wireguard-go
      wireguard-tools

      # javascript
      nodejs
      pnpm
      yarn
      bun
      deno

      # Applications
      obs-studio
      google-chrome
      discord
      (discord.override {
        withOpenASAR = true;
        withVencord = true; # For customization
      })
      firefox
      obsidian
      postman
      scrcpy
      vesktop

      # Terminal Eye Candy
      pipes

      vim
      wget
      curl
      git
      ksnip
      bash
      bash-completion
      sqlite
      vlc
      tmux
      usbutils
      htop
      wget
      lshw # see hardware info
      jq
      neofetch
    ]
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
    ])
    ++ (with latest; [
      claude-code
      devenv
      gemini-cli
      vscode
    ]);
}
