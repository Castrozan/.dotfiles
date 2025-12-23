{ latest, ... }:
{
  home.packages = with latest; [
    (code-cursor.overrideAttrs (
      old:
      let
        version = "2.2.43";
        buildId = "32cfbe848b35d9eb320980195985450f244b303d";
        hash = "WQPpLexTO9+8ZeQPFhlj/CHEbroW8azBX9Vjpr108a0=";
      in
      {
        version = version;
        src = pkgs.appimageTools.extract {
          pname = "code-cursor";
          version = version;
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
