{ pkgs, ... }:
let
  vpn-work = pkgs.stdenv.mkDerivation {
    name = "vpn-work";
    dontUnpack = true;
    dontBuild = true;

    wrapperScript = pkgs.writeScript "vpn-work" (
      pkgs.lib.replaceStrings
        [
          "@openfortivpn@"
          "@procps@"
          "@coreutils@"
          "@gnugrep@"
          "@xdgUtils@"
        ]
        [
          "${pkgs.openfortivpn}"
          "${pkgs.procps}"
          "${pkgs.coreutils}"
          "${pkgs.gnugrep}"
          "${pkgs.xdg-utils}"
        ]
        (builtins.readFile ./vpn-work.sh)
    );

    installPhase = ''
      mkdir -p $out/bin
      cp $wrapperScript $out/bin/vpn-work
      chmod +x $out/bin/vpn-work
    '';
  };
in
{
  home.packages = [
    pkgs.openfortivpn
    vpn-work
  ];
}
