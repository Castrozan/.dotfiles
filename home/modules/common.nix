# TODO: idk nothing about this file. remove or refactor it
{
  pkgs,
  unstable,
  ...
}:
{
  home.packages = with pkgs; [
    # archives
    # zip
    # unzip
    # p7zip

    # utils
    ripgrep
    yq-go # https://github.com/mikefarah/yq
    # htop

    # misc
    # libnotify
    # wineWowPackages.wayland
    # xdg-utils
    # graphviz

    # productivity
    # obsidian

    # IDE
    insomnia

    # cloud native
    docker-compose
    kubectl

    unstable.nodejs_22
    unstable.nodePackages_latest.npm
    unstable.nodePackages_latest.pnpm
    yarn

    # db related
    # dbeaver-bin
    # mycli
    # pgcli
  ];

  programs = {
    # tmux = {
    #   enable = true;
    #   clock24 = true;
    #   keyMode = "vi";
    #   extraConfig = "mouse on";
    # };

    bat = {
      enable = true;
      config = {
        pager = "less -FR";
        theme = "dracula";
      };
      themes = {
        # # https://raw.githubusercontent.com/catppuccin/bat/main/Catppuccin-mocha.tmTheme
        # catppuccin-mocha = {
        #   src = catppuccin-bat;
        #   file = "Catppuccin-mocha.tmTheme";
        # };
        dracula = {
          src = pkgs.fetchFromGitHub {
            owner = "dracula";
            repo = "sublime"; # Bat uses sublime syntax for its themes
            rev = "26c57ec282abcaa76e57e055f38432bd827ac34e";
            sha256 = "019hfl4zbn4vm4154hh3bwk6hm7bdxbr1hdww83nabxwjn99ndhv";
          };
          file = "Dracula.tmTheme";
        };
      };
    };

    # btop.enable = true; # replacement of htop/nmon
    # eza.enable = true; # A modern replacement for 'ls'
    # jq.enable = true; # A lightweight and flexible command-line JSON processor
    # ssh.enable = true;
    # aria2.enable = true;

    # skim = {
    #   enable = true;
    #   enableZshIntegration = true;
    #   defaultCommand = "rg --files --hidden";
    #   changeDirWidgetOptions = [
    #     "--preview 'exa --icons --git --color always -T -L 3 {} | head -200'"
    #     "--exact"
    #   ];
    # };
  };

  services = {
    # syncthing.enable = true;

    # auto mount usb drives
    udiskie.enable = true;
  };
}
