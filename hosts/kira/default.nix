{
  lib,
  pkgs,
  username,
  ...
}:
{
  imports = [
    ./brave
    ./wezterm
    ./displays
    ./finder
    ./window-manager
    ./symbolic-hotkeys
    ./quit-windowless-applications
    ./workspace-window-switcher
    ./rebuild
    ./karabiner
  ];
  users.users.${username} = {
    name = username;
    home = "/Users/${username}";
    shell = pkgs.fish;
  };

  system = {
    primaryUser = username;
    stateVersion = 6;
    keyboard = {
      enableKeyMapping = true;
    };
    defaults = {
      ".GlobalPreferences"."com.apple.mouse.scaling" = 3.99;
      CustomUserPreferences = {
        ".GlobalPreferences".AppleActionOnDoubleClick = "None";
        ".GlobalPreferences"."com.apple.scrollwheel.scaling" = -1;
        "com.apple.driver.AppleBluetoothMultitouch.mouse"."MouseMomentumScroll" = false;
        "com.apple.AppleMultitouchMouse"."MouseMomentumScroll" = false;
        "com.apple.AppleMultitouchTrackpad"."TrackpadFourFingerPinchGesture" = 0;
        "com.apple.AppleMultitouchTrackpad"."TrackpadFiveFingerPinchGesture" = 0;
        "com.apple.driver.AppleBluetoothMultitouch.trackpad"."TrackpadFourFingerPinchGesture" = 0;
        "com.apple.driver.AppleBluetoothMultitouch.trackpad"."TrackpadFiveFingerPinchGesture" = 0;
        "com.apple.HIToolbox" = {
          AppleEnabledInputSources = [
            {
              "Bundle ID" = "com.apple.CharacterPaletteIM";
              InputSourceKind = "Non Keyboard Input Method";
            }
            {
              InputSourceKind = "Keyboard Layout";
              "KeyboardLayout ID" = -22000;
              "KeyboardLayout Name" = "Brazilian ABNT2 Fixed";
            }
          ];
          AppleSelectedInputSources = [
            {
              InputSourceKind = "Keyboard Layout";
              "KeyboardLayout ID" = -22000;
              "KeyboardLayout Name" = "Brazilian ABNT2 Fixed";
            }
          ];
        };
      };
      NSGlobalDomain = {
        "com.apple.swipescrolldirection" = false;
        NSAutomaticWindowAnimationsEnabled = false;
        NSWindowResizeTime = 0.001;
      };
      dock = {
        autohide = true;
        autohide-delay = 1000.0;
        autohide-time-modifier = 0.0;
        expose-animation-duration = 0.1;
        show-recents = false;
        tilesize = 48;
        minimize-to-application = true;
        mru-spaces = false;
        orientation = "bottom";
        mineffect = "genie";
        magnification = false;
        launchanim = false;
        wvous-tl-corner = 1;
        wvous-tr-corner = 1;
        wvous-bl-corner = 1;
        wvous-br-corner = 14;
      };
    };
  };

  launchd.user.agents.quit-finder-on-login = {
    serviceConfig = {
      Label = "com.dotfiles.quit-finder-on-login";
      ProgramArguments = [
        "/usr/bin/osascript"
        "-e"
        "tell application \"Finder\" to quit"
      ];
      RunAtLoad = true;
      LaunchOnlyOnce = true;
    };
  };

  homebrew = {
    enable = true;
    onActivation.cleanup = "zap";
    casks = [
      "brave-browser"
      "dbeaver-community"
      "docker"
      "google-chrome"
      "obsidian"
      "wezterm"
    ];
  };

  system.activationScripts.power.text = lib.mkAfter ''
    echo "configuring pmset for both battery and AC..." >&2
    pmset -b sleep 0 displaysleep 0 disksleep 0 standby 0 autopoweroff 0 hibernatemode 0
    pmset -c sleep 0 displaysleep 0 disksleep 0 standby 0 autopoweroff 0 hibernatemode 0
  '';

  system.defaults.screensaver = {
    askForPassword = false;
    askForPasswordDelay = 0;
  };

  system.defaults.CustomUserPreferences."com.apple.screensaver".idleTime = 0;

  programs.fish.enable = true;
  programs.fish.useBabelfish = true;

  security = {
    pam.services.sudo_local.touchIdAuth = true;
    sudo.extraConfig = ''
      Cmnd_Alias NIX_DARWIN_CMDS = /run/current-system/sw/bin/darwin-rebuild, /run/current-system/sw/bin/nix, /run/current-system/sw/bin/nix-env, /run/current-system/sw/bin/nix-store, /run/current-system/sw/bin/nix-channel, /run/current-system/sw/bin/nix-build, /run/current-system/sw/bin/nix-collect-garbage, /run/current-system/sw/bin/nix-instantiate, /run/current-system/sw/bin/nix-shell, /run/current-system/sw/bin/nix-prefetch-url, /run/current-system/sw/bin/nix-hash, /run/current-system/sw/bin/nix-copy-closure, /run/current-system/sw/bin/nix-daemon, /bin/launchctl
      ${username} ALL=(ALL) NOPASSWD: NIX_DARWIN_CMDS
    '';
  };

  nix.settings = {
    trusted-users = [
      "root"
      username
    ];
    experimental-features = [
      "nix-command"
      "flakes"
    ];
  };

  nixpkgs = {
    config.allowUnfree = true;
    hostPlatform = "aarch64-darwin";
  };
}
