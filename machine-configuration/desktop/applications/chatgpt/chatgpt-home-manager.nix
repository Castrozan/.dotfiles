{
  pkgs,
  lib,
  isNixOS,
  ...
}:
let
  chatgpt = pkgs.callPackage ./package.nix { };
in
{
  config = lib.mkIf isNixOS {
    home.packages = [ chatgpt ];
    xdg.dataFile."applications/chatgpt.desktop".source =
      "${chatgpt}/share/applications/chatgpt.desktop";
  };
}
