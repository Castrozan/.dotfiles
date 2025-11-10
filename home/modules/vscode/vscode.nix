{ pkgs, ... }:
let
  vscode = pkgs.vscode.overrideAttrs (old: rec {
    version = "1.105.1";
    src = pkgs.fetchurl {
      name = "VSCode_${version}_linux-x64.tar.gz";
      url = "https://update.code.visualstudio.com/${version}/linux-x64/stable";
      sha256 = "MqZQ8aER3wA1StlXH1fRImg3Z3dnfdWvIWLq2SEGeok=";
    };
  });
in
{
  home.packages = [
    vscode
  ];
}
