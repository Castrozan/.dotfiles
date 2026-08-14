{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;

  selectedTheme = import ../../../desktop/theming/selected-theme.nix;

  herdrPageKeyRouter = "${pkgs.python3}/bin/python3 ${./scripts/route-page-key.py}";

  renderedHerdrConfig = pkgs.writeText "herdr-config.toml" (
    lib.replaceStrings
      [ "@herdr_accent@" "@herdr_page_key_router@" ]
      [ selectedTheme.accentHex herdrPageKeyRouter ]
      (builtins.readFile ./program-configuration/config.toml)
  );
in
{
  imports = [ ./herdr-config-mutable-home-manager.nix ];

  home = {
    packages = [ herdrPackage ];

    file.".config/herdr/config.toml.nix-source".source = renderedHerdrConfig;

    activation.reloadHerdrAfterConfigSeed =
      lib.hm.dag.entryAfter
        [
          "seedHerdrConfigAsMutableFile"
        ]
        ''
          ${herdrPackage}/bin/herdr server reload-config >/dev/null 2>&1 || true
        '';
  };
}
