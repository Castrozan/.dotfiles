{ pkgs }:
let
  source = pkgs.fetchurl {
    url = "https://codeload.github.com/jackwener/OpenCLI/tar.gz/c938b28b9f71d7bfa34e7da84f0f06f64820178d";
    hash = "sha256-AHQqm4GY1HIcs4Goumwq5jPhuYUvAEJXnbDeGr/CE5o=";
  };
in
pkgs.runCommand "opencli-extension-1.0.25" { } ''
  tar -xzf ${source}
  mkdir -p "$out"
  cd OpenCLI-*/extension
  cp -R manifest.json dist icons popup.html popup.js "$out/"
''
