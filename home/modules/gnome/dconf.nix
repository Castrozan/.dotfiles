{ ... }:
let
  kitty-quick-temp-shell-command = ''
    kitty --override remember_window_size=no
      --override initial_window_width=80c
      --override initial_window_height=24c
      --override window_padding_width=10
      -e tmux new-session
  '';
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
    };

    "org/gnome/shell/extensions/default-workspace" = {
      default-workspace-number = 11;
    };

    "org/gnome/shell/extensions/wsmatrix" = {
      num-columns = 7;
      num-rows = 3;
      show-popup = true;
    };

    # TODO: unbind favorite-apps and configure them manually
    # so i dont need to favorite apps
    # Disable favorite-apps keybindings
    # "org/gnome/shell/keybindings" = {
    #   switch-to-application-1 = [ ];
    # };

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
        "kitty.desktop"
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

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom6" = {
      name = "obsidian-read-it-later";
      binding = "<Super>r";
      command = "xdg-open 'obsidian://adv-uri?commandid=obsidian-read-it-later%3Asave-clipboard-to-notice'";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5" = {
      name = "daily-note";
      binding = "<Super>d";
      command = "daily-note";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom4" = {
      name = "workbench";
      binding = "<Super>w";
      command = "bash -c 'cursor $HOME/workbench'";
    };

    # custom2

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom3" = {
      name = "clipse";
      binding = "<Super>v";
      command = "kitty -e clipse";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1" = {
      name = "kitty-quick-temp-shell";
      binding = "<Shift><Alt>2";
      command = kitty-quick-temp-shell-command;
    };

    # Fixed: using forked repository with beepy 1.0.9 fix
    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0" = {
      binding = "<Alt>a";
      command = "nix run github:Castrozan/whisper-input";
      name = "whisper";
    };

    # Window manager keybindings
    "org/gnome/desktop/wm/keybindings" = {
      close = [ "<Shift><Control>w" ];
      switch-applications = [ ];
      switch-applications-backward = [ ];
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
