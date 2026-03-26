{ pkgs, ... }:
let
  vscodeLinuxPinnedBuild = pkgs.vscode.overrideAttrs (previousAttributes: rec {
    version = "1.112.0";
    src = pkgs.fetchurl {
      name = "VSCode_${version}_linux-x64.tar.gz";
      url = "https://update.code.visualstudio.com/${version}/linux-x64/stable";
      sha256 = "VyjqPTyLn8eGh/XS3nn0PMqiAsrL91vDZD6Z9L2oh24=";
    };
    buildInputs =
      previousAttributes.buildInputs
      ++ (with pkgs; [
        curl
        openssl
        libsoup_3
        webkitgtk_4_1
      ]);
  });

  vscodePackage = vscodeLinuxPinnedBuild;
in
{
  home.packages = [
    vscodePackage
  ];
}
