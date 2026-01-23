{ pkgs, ... }:
let
  version = "0.0.22";
  sha256 = "1h5c21i5rdzsrivzdwknwk18zvvrgmghi1kdamnpsdd9209bsdkj";
in
{
  home.packages = [
    (pkgs.appimageTools.wrapType2 {
      pname = "bananas";
      inherit version;
      src = pkgs.fetchurl {
        url = "https://github.com/mistweaverco/bananas/releases/download/v${version}/bananas_x86_64.AppImage";
        inherit sha256;
      };
    })
  ];
}
