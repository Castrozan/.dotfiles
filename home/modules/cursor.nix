{ latest, ... }:
{
  home.packages = with latest; [
    code-cursor
    # (code-cursor.overrideAttrs (
    #   old:
    #   let
    #     version = "1.6.35";
    #     buildId = "b753cece5c67c47cb5637199a5a5de2b7100c18f";
    #     sha256 = "sha256-62u8snx9nbJtsg7uROZNVzo3macrkTghTCep943e8+I=";
    #   in
    #   {
    #     version = version;
    #     src = pkgs.appimageTools.extract {
    #       pname = "code-cursor";
    #       version = version;
    #       src = pkgs.fetchurl {
    #         sha256 = sha256;
    #         url =
    #           "https://downloads.cursor.com/production/"
    #           + buildId
    #           + "/linux/x64/Cursor-"
    #           + version
    #           + "-x86_64.AppImage";
    #       };
    #     };
    #     sourceRoot = "code-cursor-" + version + "-extracted/usr/share/cursor";
    #   }
    # ))
  ];
}
