{ pkgs }:
pkgs.vscode.overrideAttrs (previousAttributes: rec {
  version = "1.143.1";
  src = pkgs.fetchurl {
    name = "VSCode_${version}_linux-x64.tar.gz";
    url = "https://update.code.visualstudio.com/${version}/linux-x64/stable";
    sha256 = "sha256-SPZYBS5U4CChwb57N6wPmuOfB+jM2oBcY/BTz9pysr4=";
  };
  buildInputs =
    previousAttributes.buildInputs
    ++ (with pkgs; [
      curl
      openssl
      libsoup_3
      webkitgtk_4_1
    ]);
})
