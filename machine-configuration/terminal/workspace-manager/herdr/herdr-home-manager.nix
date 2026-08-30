{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;

  selectedTheme = import ../../../desktop/theming/selected-theme.nix;

  renderedHerdrConfig = pkgs.writeText "herdr-config.toml" (
    lib.replaceStrings [ "@herdr_accent@" ] [ selectedTheme.accentHex ] (
      builtins.readFile ./program-configuration/config.toml
    )
  );
in
{
  imports = [
    ./herdr-config-mutable-home-manager.nix
    ./herdr-service-home-manager.nix
  ];

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
