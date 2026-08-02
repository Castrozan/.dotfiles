{
  pkgs,
  lib,
  config,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  opencodeStateDirectory = "${homeDir}/.local/state/opencode";

  opencodeTuiSettings = {
    "$schema" = "https://opencode.ai/tui.json";
    theme = "kanagawa";
    mouse = true;
    diff_style = "auto";

    keybinds = {
      messages_undo = "ctrl+e,<leader>u";
    };

    attention = {
      enabled = true;
      notifications = true;
      sound = false;
      volume = 0.4;
    };

    prompt = {
      max_width = "auto";
    };
  };

  seedOpencodeSidebarHidden = pkgs.writeShellScript "seed-opencode-sidebar-hidden" ''
    export PATH="${pkgs.jq}/bin:${pkgs.moreutils}/bin:$PATH"
    exec ${./scripts/seed_opencode_sidebar_hidden.sh} "${opencodeStateDirectory}/kv.json"
  '';
in
{
  home.file.".config/opencode/tui.json".text = builtins.toJSON opencodeTuiSettings;

  home.activation.seedOpencodeSidebarHiddenByDefault = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${seedOpencodeSidebarHidden}
  '';
}
