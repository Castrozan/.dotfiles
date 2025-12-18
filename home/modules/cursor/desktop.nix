{ pkgs, ... }:
let
  cursorIcon = pkgs.stdenv.mkDerivation {
    name = "cursor-icon";
    src = ./favicon.ico;
    dontUnpack = true;
    installPhase = ''
      mkdir -p $out
      cp $src $out/favicon.ico
    '';
  };
in
{
  xdg.desktopEntries.cursor = {
    name = "Cursor";
    exec = "cursor %F";
    icon = "${cursorIcon}/favicon.ico";
    type = "Application";
    categories = [
      "Development"
      "IDE"
    ];
    comment = "AI-first code editor";
  };
}
