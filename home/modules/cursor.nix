{ latest, ... }:
{
  home.packages = with latest; [
    # code-cursor
    (code-cursor.overrideAttrs (
      old:
      let
        version = "1.4.5";
        sha256 = "sha256-2Hz1tXC+YkIIHWG1nO3/84oygH+wvaUtTXqvv19ZAz4=";
        buildId = "af58d92614edb1f72bdd756615d131bf8dfa5299";
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
