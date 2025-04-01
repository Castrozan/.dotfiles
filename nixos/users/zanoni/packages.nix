#
# TODO: move this to home manager packages
#
{ pkgs, ... }:
{
  # List packages installed in system profile. To search, run: nix search wget
  environment.systemPackages = with pkgs; [
    # TCC tools
    pandoc
    haskellPackages.citeproc
    texlive.combined.scheme-full
    texliveTeTeX

    # Development Tools
    alejandra
    azure-cli
    dbeaver-bin
    docker
    gh
    git
    gnumake
    k6
    lazydocker
    lazygit
    nixd
    nixpkgs-fmt
    nix-prefetch-github
    terraform

    # Python and Dependencies
    python312
    python312Packages.fastapi
    python312Packages.httpx
    python312Packages.pip
    python312Packages.pydantic
    python312Packages.uv
    python312Packages.uvicorn

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
    wget
    xsel # Required for tmux yank
    yazi
    zip
    zsh

    # Network Tools
    linuxKernel.packages.linux_5_4.wireguard
    wgnord # Note: Should install manually from github.com/phirecc/wgnord
    wireguard-go
    wireguard-tools

    # Applications
    brave
    google-chrome
    discord
    (discord.override {
      withOpenASAR = true;
      withVencord = true; # For customization
    })
    firefox
    obsidian
    (opera.override {
      proprietaryCodecs = true; # Enables video playback
    })
    postman
    scrcpy
    vesktop

    # Terminal Eye Candy
    cbonsai
    pipes
  ];
}
