{ pkgs, ... }:
let
  vscode = pkgs.vscode.overrideAttrs (old: rec {
    version = "1.99.3";
    src = pkgs.fetchurl {
      name = "VSCode_${version}_linux-x64.tar.gz";
      url = "https://update.code.visualstudio.com/${version}/linux-x64/stable";
      sha256 = "tP9frbQweLpJVhiBbwIvuFm87IHCC7LT9pNT3V10ODU=";
    };
  });
in
{
  home.packages = [
    vscode
  ];
}
