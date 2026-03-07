# openfortivpn - FortiGate VPN client with SAML support
# Alternative to FortiClient GUI which doesn't work on Hyprland
{ pkgs, ... }:
let
  vpn-betha = pkgs.stdenv.mkDerivation {
    name = "vpn-betha";
    dontUnpack = true;
    dontBuild = true;

    wrapperScript = pkgs.writeScript "vpn-betha" (
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
        (builtins.readFile ./vpn-betha.sh)
    );

    installPhase = ''
      mkdir -p $out/bin
      cp $wrapperScript $out/bin/vpn-betha
      chmod +x $out/bin/vpn-betha
    '';
  };
in
{
  home.packages = [
    pkgs.openfortivpn
    vpn-betha
  ];
}
