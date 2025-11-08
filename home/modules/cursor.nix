{ latest, ... }:
{
  home.packages = with latest; [
    # code-cursor
    (code-cursor.overrideAttrs (
      old:
      let
        version = "2.0.69";
        buildId = "63fcac100bd5d5749f2a98aa47d65f6eca61db39";
        sha256 = "sha256-dwhYqX3/VtutxDSDPoHicM8D/sUvkWRnOjrSOBPiV+s=";
      in
      {
        version = version;
        src = pkgs.appimageTools.extract {
          pname = "code-cursor";
          version = version;
          src = pkgs.fetchurl {
            sha256 = sha256;
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
