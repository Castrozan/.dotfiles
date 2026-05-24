{
  config,
  pkgs,
  ...
}:
let
  karabinerRulesList = import ../rules { inherit (config.home) username; };

  karabinerProfileContainingRules = {
    profiles = [
      {
        name = "Default";
        selected = true;
        virtual_hid_keyboard.keyboard_type_v2 = "ansi";
        complex_modifications.rules = karabinerRulesList;
      }
    ];
  };

  karabinerJsonInNixStore = pkgs.writeText "karabiner.json" (
    builtins.toJSON karabinerProfileContainingRules
  );
in
{
  home.activation.copyKarabinerRulesJsonToUserConfigDirectory =
    config.lib.dag.entryAfter [ "writeBoundary" ]
      ''
        export SOURCE_KARABINER_JSON=${karabinerJsonInNixStore}
        ${builtins.readFile ./scripts/copy-karabiner-json-to-user-config.sh}
      '';
}
