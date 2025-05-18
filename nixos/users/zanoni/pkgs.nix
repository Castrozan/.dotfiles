{ pkgs, ... }:
{
  # List of pkgs available in nixpkgs. To search, run: nix search wget
  environment.systemPackages = with pkgs; [
    # TCC tools
    gdrive3
    pandoc_3_5
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
    ffmpeg
    fzf
    htop
    p7zip
    tmux
    unzip
    vim
    wget
    xclip
    xsel # Required for tmux yank
    yazi
    zip
    zoxide
    zsh

    # Network Tools
    linuxKernel.packages.linux_5_4.wireguard
    wgnord # Note: Should install manually from github.com/phirecc/wgnord
    wireguard-go
    wireguard-tools

    # Applications
    # brave # using the unstable channel
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
    cmatrix

    vim
    wget
    curl
    git
    bash
    bash-completion
    vlc
    tmux
    usbutils
    htop
    wget
    # see hardware info
    lshw
    jq
    # sysstat
    # lm_sensors # for `sensors` command
    # minimal screen capture tool, used by i3 blur lock to take a screenshot
    # print screen key is also bound to this tool in i3 config
    # scrot
    neofetch
  ];
}
