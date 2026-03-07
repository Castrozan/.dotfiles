{ latest, pkgs, ... }:
{
  home.packages = with latest; [
    (code-cursor.overrideAttrs (
      _:
      let
        version = "2.3.30";
        buildId = "d1289018cc3fcc395487f65455e31651734308d7";
        hash = "0MOAyPJWilqvmsJYz4+q/wvzZ42sUpWDVaKSTJ74fvA=";
      in
      {
        inherit version;
        src = pkgs.appimageTools.extract {
          pname = "code-cursor";
          inherit version;
          src = pkgs.fetchurl {
            sha256 = "sha256-" + hash;
            url =
              "https://downloads.cursor.com/production/"
              + buildId
              + "/linux/x64/Cursor-"
              + version
              + "-x86_64.AppImage";
          };
        };
        sourceRoot = "code-cursor-" + version + "-extracted/usr/share/cursor";
      }
    ))
  ];
}
