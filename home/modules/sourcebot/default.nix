{ pkgs, config, ... }:
let
  homeDir = config.home.homeDirectory;
  dataDir = "${homeDir}/.local/share/sourcebot";

  wrapperScript = pkgs.writeScript "sourcebot-wrapper.sh" (
    pkgs.lib.replaceStrings
      [
        "@docker@"
        "@coreutils@"
        "@gnugrep@"
        "@dataDir@"
      ]
      [
        "${pkgs.docker}"
        "${pkgs.coreutils}"
        "${pkgs.gnugrep}"
        dataDir
      ]
      (builtins.readFile ./sourcebot.sh)
  );

  sourcebot = pkgs.stdenv.mkDerivation {
    name = "sourcebot";
    dontUnpack = true;
    dontBuild = true;
    installPhase = ''
      mkdir -p $out/bin
      cp ${wrapperScript} $out/bin/sourcebot
      chmod +x $out/bin/sourcebot
    '';
  };
in
{
  home.packages = [ sourcebot ];
}
