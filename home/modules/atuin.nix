{ pkgs, ... }:
{
  programs.atuin = {
    enable = true;
    package = pkgs.atuin;
    enableFishIntegration = true;
    enableBashIntegration = true;
    flags = [ "--disable-up-arrow" ];
    settings = {
      auto_sync = false;
      sync_frequency = "0";
      search_mode = "fuzzy";
      filter_mode = "global";
      filter_mode_shell_up_key_binding = "directory";
      style = "compact";
      inline_height = 20;
      show_preview = true;
      history_filter = [
        "^cd "
        "^ls"
        "^exit$"
      ];
    };
  };
}
