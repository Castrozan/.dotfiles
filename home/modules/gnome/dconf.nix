_:
let
  # Use explicit socket path to ensure all tmux commands use the same server
  # XDG_RUNTIME_DIR/tmux-$UID/default is the standard location for user sessions
  wezterm-quick-temp-shell-command = "wezterm start -- bash -c 'tmux -S \"$XDG_RUNTIME_DIR/tmux-$(id -u)/default\" new-session'";
in
{
  # GNOME settings
  dconf.settings = {
    "org/gnome/desktop/peripherals/mouse" = {
      natural-scroll = false;
      speed = -0.9;
    };

    "org/gnome/desktop/interface" = {
      font-hinting = "slight";
      enable-hot-corners = true;
      clock-show-weekday = true;
      clock-show-seconds = true;
      gtk-theme = "Yaru-viridian-dark";
      icon-theme = "Yaru-viridian";
      color-scheme = "prefer-dark";
      cursor-theme = "Adwaita";
      cursor-size = 24;
      show-battery-percentage = true;
    };

    "org/gnome/desktop/background" = {
      color-shading-type = "solid";
      picture-options = "zoom";
      # TODO: the bkg image does not apply itself, need to fix select it on gnome settings
      picture-uri = "file:///home/zanoni/.dotfiles/static/alter-jellyfish-dark.jpg";
      picture-uri-dark = "file:///home/zanoni/.dotfiles/static/alter-jellyfish-dark.jpg";
      primary-color = "#000000000000";
      secondary-color = "#000000000000";
    };

    "org/gnome/desktop/screensaver" = {
      picture-uri = "file:///home/zanoni/.dotfiles/static/alter-jellyfish-dark.jpg";
      lock-delay = 0;
    };

    "org/gnome/shell/extensions/default-workspace" = {
      default-workspace-number = 11;
    };

    "org/gnome/shell/extensions/wsmatrix" = {
      num-columns = 7;
      num-rows = 3;
      show-popup = true;
      show-overview-grid = true;
      show-workspace-names = false;
      workspace-overview-toggle = [ "" ]; # Disable default Super+W keybinding
    };

    "org/gnome/shell/keybindings" = {
      # Disable Super+v for notification list
      toggle-message-tray = [ ];
      # Screenshot keybindings - use GNOME's interactive screenshot UI - pipe to ksnip for annotation
      show-screenshot-ui = [ "Print" ];
      screenshot = [ ];
      screenshot-window = [ ];
      show-screen-recording-ui = [ ];
    };

    "org/gnome/shell" = {
      disable-user-extensions = false;
      # Enable Super+1,2,3... to launch them
      favorite-apps = [
        "brave-browser.desktop"
        "wezterm.desktop"
      ];
      # Extensions are installed via home.packages (see users/*/pkgs.nix)
      enabled-extensions = [
        "default-workspace@mateusrodcosta.com"
        "wsmatrix@martin.zurowietz.de"
      ];
    };

    "org/gnome/settings-daemon/plugins/media-keys" = {
      # Disable default GNOME screenshot shortcuts so custom keybindings can work
      # These defaults take precedence over custom keybindings, so we must disable them first
      screenshot = [ ];
      area-screenshot = [ ];
      window-screenshot = [ ];
      screencast = [ ];

      custom-keybindings = [
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/"
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/"
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom2/"
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom3/"
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom4/"
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5/"
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom6/"
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom7/"
      ];
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom7" = {
      name = "screenshot-annotate";
      binding = "<Shift>Print";
      command = "ksnip-annotate";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5" = {
      name = "voxtype-toggle";
      binding = "<Shift><Alt>a";
      command = "bash -c 'if pgrep -f \"voxtype record start\" > /dev/null; then voxtype record stop; else voxtype record start; fi'";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom6" = {
      name = "obsidian-read-it-later";
      binding = "<Super>r";
      command = "xdg-open 'obsidian://adv-uri?commandid=obsidian-read-it-later%3Asave-clipboard-to-notice'";
    };

    # Set OBSIDIAN_HOME env var since gsd-media-keys doesn't have access to session variables
    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom4" = {
      name = "daily-note";
      binding = "<Super>d";
      command = "bash -c 'OBSIDIAN_HOME=\"$HOME/vault\" daily-note'";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom2" = {
      name = "workbench";
      binding = "<Super>w";
      command = "bash -c 'cursor $HOME/workbench'";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom3" = {
      name = "clipse";
      binding = "<Super>v";
      command = "wezterm start -- clipse";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1" = {
      name = "wezterm-quick-temp-shell";
      binding = "<Shift><Alt>2";
      command = wezterm-quick-temp-shell-command;
    };

    # TODO: gnome keeps asking for remote control to write to the screen
    # No option to remove this. https://gitlab.gnome.org/GNOME/xdg-desktop-portal-gnome/-/issues/114
    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0" = {
      binding = "<Alt>a";
      command = "whisper-input";
      name = "whisper";
    };

    "org/gnome/desktop/wm/keybindings" = {
      close = [ "<Shift><Control>w" ];
      switch-applications = [ ];
      switch-applications-backward = [ ];
      show-desktop = [ ]; # Disable Super+D
      switch-windows = [
        "<Alt>Tab"
        "<Super>Tab"
      ];
      switch-windows-backward = [
        "<Shift><Alt>Tab"
        "<Shift><Super>Tab"
      ];
    };
  };
}
