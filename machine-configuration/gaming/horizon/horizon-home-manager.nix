{ pkgs, ... }:
let
  pname = "horizon-launcher";
  version = "0.2.49";
  src = pkgs.fetchurl {
    url = "https://github.com/horizon-rust/horizon/releases/download/launcher%40${version}/horizon-launcher-linux-x86_64.AppImage";
    hash = "sha256-wePEii/SrykbSls99LY6BzpiHTUrJ4IFdcLK0ndk25E=";
  };
  extractedAppImage = pkgs.appimageTools.extract { inherit pname version src; };
in
{
  home.packages = [
    (pkgs.appimageTools.wrapType2 {
      inherit pname version src;
      extraPkgs = fhsPackages: [
        fhsPackages.gcc
        fhsPackages.pkg-config
        fhsPackages.alsa-lib.dev
        fhsPackages.systemd.dev
      ];
      extraInstallCommands = ''
        install -Dm444 ${extractedAppImage}/horizon-launcher.desktop $out/share/applications/horizon-launcher.desktop
        install -Dm444 ${extractedAppImage}/horizon.png $out/share/icons/hicolor/512x512/apps/horizon.png
      '';
    })
  ];
}
