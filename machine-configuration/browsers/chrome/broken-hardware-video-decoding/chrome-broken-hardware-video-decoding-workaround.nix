{ pkgs, chromePackage }:
let
  inherit (pkgs) lib;

  flagsThatStopChromeAdvertisingCodecsItCannotDecode = [ "--disable-accelerated-video-decode" ];

  chromeWithoutBrokenHardwareVideoDecoding = pkgs.symlinkJoin {
    name = "google-chrome-without-broken-hardware-video-decoding";
    paths = [ chromePackage ];
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      rm "$out/bin/google-chrome-stable"
      makeWrapper "${chromePackage}/bin/google-chrome-stable" "$out/bin/google-chrome-stable" \
        --add-flags "${lib.concatStringsSep " " flagsThatStopChromeAdvertisingCodecsItCannotDecode}"
    '';
  };
in
{
  inherit flagsThatStopChromeAdvertisingCodecsItCannotDecode chromeWithoutBrokenHardwareVideoDecoding;
}
