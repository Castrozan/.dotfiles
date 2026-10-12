{
  publicReference,
  system,
  component,
}:
let
  publicFlake = builtins.getFlake publicReference;
  inherit (publicFlake.inputs.dependencies) inputs;
  pkgs = import inputs.nixpkgs {
    inherit system;
    config.allowUnfree = true;
  };
  latest = import inputs.nixpkgs-latest {
    inherit system;
    config.allowUnfree = true;
  };
  source = publicFlake.outPath;
  llamaModule =
    import
      (source + "/machine-configuration/development/local-language-models/llama-cpp-home-manager.nix")
      {
        inherit pkgs latest;
        inherit (pkgs) lib;
        config = { };
        isNixOS = true;
      };
  latestPackages =
    with latest;
    [
      brave
      gemini-cli
      vscode
      bun
      google-chrome
      prismlauncher
      vial
      yt-dlp
      (import (source + "/machine-configuration/machines/chise/system/vivaldi-codec-lib-path-fixed.nix") {
        vivaldiPackages = latest;
      })
      (import (source + "/machine-configuration/terminal/emulators/wezterm/patched-wezterm.nix") {
        inherit latest;
      })
    ]
    ++ llamaModule.config.content.home.packages
    ++ (import (source + "/machine-configuration/editors/cursor/cursor-package-home-manager.nix") {
      inherit pkgs latest;
    }).home.packages;
  components = {
    devenv =
      if pkgs.stdenv.hostPlatform.isLinux then
        publicFlake.packages.${system}.devenv.drvPath
      else
        inputs.devenv.packages.${system}.devenv.drvPath;
    test_environment =
      (import (source + "/machine-configuration/development/testing/test-suite-environment.nix") {
        inherit pkgs;
      }).drvPath;
    latest_selected = map (package: package.drvPath) latestPackages;
  };
in
components.${component}
