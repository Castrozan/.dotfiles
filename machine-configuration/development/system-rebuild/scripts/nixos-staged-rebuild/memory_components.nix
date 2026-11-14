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
  latestPackages = with latest; [
    brave
    gemini-cli
    vscode
    bun
    google-chrome
    prismlauncher
    vial
    yt-dlp
    (import (source + "/machine-configuration/terminal/emulators/wezterm/patched-wezterm.nix") {
      inherit latest;
    })
  ];
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
