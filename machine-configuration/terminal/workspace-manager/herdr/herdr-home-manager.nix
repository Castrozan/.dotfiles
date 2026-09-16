{
  pkgs,
  lib,
  inputs,
  config,
  ...
}:
let
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
  herdrClientTools = import ./herdr-client-package.nix {
    inherit pkgs herdrPackage;
  };

  selectedTheme = import ../../../desktop/appearance/theming/selected-theme.nix;

  renderedHerdrConfig = pkgs.writeText "herdr-config.toml" (
    lib.replaceStrings [ "@herdr_accent@" ] [ selectedTheme.accentHex ] (
      builtins.readFile ./program-configuration/config.toml
    )
  );
in
{
  imports = [
    ./herdr-pace-home-manager.nix
    ./herdr-config-mutable-home-manager.nix
    ./herdr-service-home-manager.nix
  ];

  home = {
    packages = [ herdrClientTools.package ];

    file.".config/herdr/config.toml.nix-source".source = renderedHerdrConfig;

    activation = {
      reloadHerdrAfterConfigSeed =
        lib.hm.dag.entryAfter
          [
            "seedHerdrConfigAsMutableFile"
          ]
          ''
            ${herdrClientTools.package}/bin/herdr server reload-config >/dev/null 2>&1 || true
          '';

      refreshHerdrAgentIntegrations =
        lib.hm.dag.entryAfter
          [
            "linkGeneration"
            "seedCodexConfigAsMutableFile"
          ]
          ''
            run ${herdrPackage}/bin/herdr integration install codex
            run ${herdrPackage}/bin/herdr integration install opencode
            ${lib.optionalString (config ? hermes) ''
              run mkdir -p "$HOME/.hermes"
              run ${herdrPackage}/bin/herdr integration install hermes
            ''}
          '';

      retainRunningHerdrPackage = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${herdrClientTools.selector}/bin/select-herdr-client retain-running ${herdrPackage}/bin/herdr
      '';
    };
  };
}
