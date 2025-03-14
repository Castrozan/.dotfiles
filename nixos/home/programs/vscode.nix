#
# Enable vscode with config to set a specific version
#
{ pkgs, ... }:
let
  vscode = pkgs.vscode.overrideAttrs (old: rec {
    version = "1.92.0";
    src = pkgs.fetchurl {
      name = "VSCode_${version}_linux-x64.tar.gz";
      url = "https://update.code.visualstudio.com/${version}/linux-x64/stable";
      sha256 = "ZLTNUk+CFjuWwALSCWL6HOsjPrRgoAvNUUNiyiHOE+E=";
    };
  });
in
{
  home.packages = [
    vscode
  ];
}
