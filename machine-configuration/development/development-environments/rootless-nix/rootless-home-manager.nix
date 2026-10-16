{
  pkgs,
  username,
  homeDirectory,
  home-version,
  ...
}:
{
  # Headless standalone profile: no host services, account changes or credentials.
  home = {
    inherit username homeDirectory;
    stateVersion = home-version;
    packages = [
      (pkgs.callPackage
        ../../../../agent-harness/agent-to-agent-communication/client/fleet-client-package.nix
        { }
      )
      (import ../../../media/media-generation/speech-cloud-package.nix { inherit pkgs; })
    ]
    ++ (with pkgs; [
      gh
      openssh
      age
      jq
      ripgrep
      fd
      bat
      tree
      curl
      wget
      unzip
      zip
      file
      nano
      python312
      nodejs_22
      shellcheck
      nixfmt-rfc-style
    ]);
    sessionVariables = {
      EDITOR = "nano";
      PAGER = "less";
    };
  };
  programs = {
    home-manager.enable = true;
    bash = {
      enable = true;
      enableCompletion = true;
      # Host /etc/profile may reset PATH before the managed user profile runs.
      profileExtra = ''
        export PATH="$HOME/.nix-profile/bin:$PATH"
      '';
    };
    git = {
      enable = true;
      settings.init.defaultBranch = "main";
    };
    fzf = {
      enable = true;
      enableBashIntegration = true;
    };
    zoxide = {
      enable = true;
      enableBashIntegration = true;
    };
    tmux = {
      enable = true;
      terminal = "screen-256color";
      historyLimit = 10000;
    };
    less.enable = true;
  };
  systemd.user.enable = false;
  xdg.enable = true;
}
