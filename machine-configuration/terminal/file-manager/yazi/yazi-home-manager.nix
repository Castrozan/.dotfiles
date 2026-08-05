{ lib, ... }:
{
  programs.yazi = {
    enable = true;

    enableBashIntegration = true;
    enableFishIntegration = false;

    settings = {
      mgr = {
        show_hidden = true;
        ratio = [
          2
          4
          3
        ];
        show_symlink = true;
      };

      which = {
        sort_by = "key";
        sort_sensitive = false;
        sort_reverse = false;
        sort_translit = false;
      };
    };

    keymap = {
      mgr.prepend_keymap =
        (import ./program-configuration/manager-keymap-navigation-and-file-operations.nix)
        ++ (import ./program-configuration/manager-keymap-selection-view-and-tabs.nix);
      help.prepend_keymap = import ./program-configuration/help-keymap.nix;
    };

    theme = lib.mkForce (
      {
        mgr = import ./program-configuration/manager-pane-theme.nix;
        status = import ./program-configuration/status-bar-theme.nix;
      }
      // (import ./program-configuration/widget-and-filetype-themes.nix)
    );
  };
}
