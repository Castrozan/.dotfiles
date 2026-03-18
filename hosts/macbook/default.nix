{
  lib,
  pkgs,
  username,
  ...
}:
{
  imports = [
    ./yabai.nix
    ./skhd.nix
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
      userKeyMapping = [
        {
          HIDKeyboardModifierMappingSrc = 30064771121;
          HIDKeyboardModifierMappingDst = 30064771124;
        }
      ];
    };
    defaults = {
      ".GlobalPreferences"."com.apple.mouse.scaling" = 3.63;
      CustomUserPreferences = {
        ".GlobalPreferences".AppleActionOnDoubleClick = "None";
        ".GlobalPreferences"."com.apple.scrollwheel.scaling" = -1;
        "com.apple.driver.AppleBluetoothMultitouch.mouse"."MouseMomentumScroll" = false;
        "com.apple.AppleMultitouchMouse"."MouseMomentumScroll" = false;
        "com.apple.AppleMultitouchTrackpad"."TrackpadFourFingerPinchGesture" = 0;
        "com.apple.AppleMultitouchTrackpad"."TrackpadFiveFingerPinchGesture" = 0;
        "com.apple.driver.AppleBluetoothMultitouch.trackpad"."TrackpadFourFingerPinchGesture" = 0;
        "com.apple.driver.AppleBluetoothMultitouch.trackpad"."TrackpadFiveFingerPinchGesture" = 0;
        "com.lwouis.alt-tab-macos" = {
          appsToShow = 0;
          spacesToShow = 1;
          showMinimizedWindows = 2;
          holdShortcut = "⌘";
          hideStatusIcons = true;
        };
      };
      NSGlobalDomain = {
        AppleInterfaceStyle = "Dark";
        "com.apple.swipescrolldirection" = false;
        NSAutomaticWindowAnimationsEnabled = false;
        NSWindowResizeTime = 0.001;
      };
      dock = {
        autohide = true;
        autohide-delay = 0.0;
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
      finder.QuitMenuItem = true;
    };
  };

  system.activationScripts.postActivation.text = ''
    osascript -e 'tell application "System Events" to tell every desktop to set picture to "/Users/${username}/.dotfiles/static/alter-jellyfish-dark.jpg"' || true
  '';

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
      "alt-tab"
      "brave-browser"
    ];
  };

  system.activationScripts.power.text = lib.mkAfter ''
    echo "configuring pmset for both battery and AC..." >&2
    pmset -b sleep 0 displaysleep 0
    pmset -c sleep 0 displaysleep 0
  '';

  system.defaults.screensaver = {
    askForPassword = false;
    askForPasswordDelay = 0;
  };

  programs.fish.enable = true;
  programs.fish.useBabelfish = true;

  security = {
    pam.services.sudo_local.touchIdAuth = true;
    sudo.extraConfig = ''
      ${username} ALL=(ALL) NOPASSWD: ALL
    '';
  };

  nix.settings.trusted-users = [
    "root"
    username
  ];

  nixpkgs = {
    config.allowUnfree = true;
    hostPlatform = "aarch64-darwin";
  };
}
