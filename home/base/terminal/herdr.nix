{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;

  selectedTheme = import ../desktop/theming/selected-theme.nix;

  herdrConfigWithThemeAccent = pkgs.writeText "herdr-config.toml" (
    lib.replaceStrings [ "@herdr_accent@" ] [ selectedTheme.accentHex ] (
      builtins.readFile ../../../.config/herdr/config.toml
    )
  );
in
{
  imports = [ ./herdr/make-config-mutable.nix ];

  home.packages = [ herdrPackage ];

  home.file.".config/herdr/config.toml.nix-source".source = herdrConfigWithThemeAccent;

  home.activation.reloadHerdrAfterConfigSeed =
    lib.hm.dag.entryAfter
      [
        "seedHerdrConfigAsMutableFile"
      ]
      ''
        ${herdrPackage}/bin/herdr server reload-config >/dev/null 2>&1 || true
      '';
}
