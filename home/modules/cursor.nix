{ latest, ... }:
{
  home.packages = with latest; [
    # code-cursor
    (code-cursor.overrideAttrs (
      old:
      let
        version = "2.1.42";
        buildId = "2e353c5f5b30150ff7b874dee5a87660693d9de6";
        sha256 = "sha256-UqHi9QlQSaOJZWW6bmElDrK5GaEGT3kU5LsXg2LUeHg=";
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
