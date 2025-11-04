{ latest, ... }:
{
  home.packages = with latest; [
    # code-cursor
    (code-cursor.overrideAttrs (
      old:
      let
        version = "2.0.34";
        buildId = "45fd70f3fe72037444ba35c9e51ce86a1977ac11";
        sha256 = "sha256-x51N2BttMkfKwH4/Uxn/ZNFVPZbaNdsZm8BFFIMmxBM=";
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
