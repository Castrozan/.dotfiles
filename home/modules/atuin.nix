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
