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

  seedSidebarHiddenByDefault = pkgs.writeShellScript "seed-opencode-sidebar-hidden" ''
    set -euo pipefail
    KV_FILE="${opencodeStateDirectory}/kv.json"
    if [ ! -d "${opencodeStateDirectory}" ]; then
      mkdir -p "${opencodeStateDirectory}"
    fi
    if [ ! -f "$KV_FILE" ]; then
      echo '{"sidebar":"hide"}' > "$KV_FILE"
      exit 0
    fi
    ${pkgs.jq}/bin/jq 'if has("sidebar") then . else . + {"sidebar":"hide"} end' "$KV_FILE" | ${pkgs.moreutils}/bin/sponge "$KV_FILE"
  '';
in
{
  home.file.".config/opencode/tui.json".text = builtins.toJSON opencodeTuiSettings;

  home.activation.seedOpencodeSidebarHiddenByDefault = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${seedSidebarHiddenByDefault}
  '';
}
