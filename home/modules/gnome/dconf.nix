_:
let
  wezterm-quick-temp-shell-command = "wezterm start -- tmux new-session";
in
{
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
      cursor-size = 24;
      show-battery-percentage = true;
    };

    "org/gnome/desktop/background" = {
      color-shading-type = "solid";
      picture-options = "zoom";
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
      workspace-overview-toggle = [ "" ];
    };

    "org/gnome/shell/keybindings" = {
      toggle-message-tray = [ ];
      show-screenshot-ui = [ "Print" ];
      screenshot = [ ];
      screenshot-window = [ ];
      show-screen-recording-ui = [ ];
    };

    "org/gnome/shell" = {
      disable-user-extensions = false;
      favorite-apps = [
        "brave-browser.desktop"
        "wezterm.desktop"
      ];
      enabled-extensions = [
        "default-workspace@mateusrodcosta.com"
        "wsmatrix@martin.zurowietz.de"
      ];
    };

    "org/gnome/settings-daemon/plugins/media-keys" = {
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

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom4" = {
      name = "daily-note";
      binding = "<Super>d";
      command = "bash -c 'OBSIDIAN_HOME=\"$HOME/vault\" daily-note'";
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom2" = {
      name = "workbench";
      binding = "<Super>w";
      command = "bash -c '$EDITOR $HOME/workbench'";
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

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0" = {
      binding = "<Alt>a";
      command = "whisp-away start";
      name = "whisp-away";
    };

    "org/gnome/desktop/wm/keybindings" = {
      close = [ "<Shift><Control>w" ];
      switch-applications = [ ];
      switch-applications-backward = [ ];
      show-desktop = [ ];
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
