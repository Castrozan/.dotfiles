{ latest, ... }:
{
  home.packages = with latest; [
    # code-cursor
    (code-cursor.overrideAttrs (old: {
      version = "1.4.5";
      src = pkgs.appimageTools.extract {
        pname = "code-cursor";
        version = "1.4.5";
        src = pkgs.fetchurl {
          url = "https://downloads.cursor.com/production/af58d92614edb1f72bdd756615d131bf8dfa5299/linux/x64/Cursor-1.4.5-x86_64.AppImage";
          sha256 = "sha256-2Hz1tXC+YkIIHWG1nO3/84oygH+wvaUtTXqvv19ZAz4=";
        };
      };
      sourceRoot = "code-cursor-1.4.5-extracted/usr/share/cursor";
    }))
  ];
}
