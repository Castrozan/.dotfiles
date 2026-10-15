{
  pkgs,
  latest,
  hostname,
}:
let
  chromeWithMachineVideoDecoding =
    if hostname == "chise" then
      import ./amd-hardware-video-decoding/chrome-amd-hardware-video-decoding.nix {
        inherit pkgs;
        chromePackage = latest.google-chrome;
        mesaPackage = latest.mesa;
      }
    else
      (import ./broken-hardware-video-decoding/chrome-broken-hardware-video-decoding-workaround.nix {
        inherit pkgs;
        chromePackage = latest.google-chrome;
      }).chromeWithoutBrokenHardwareVideoDecoding;
in
(import ./broken-mipmap-generation/chrome-broken-mipmap-generation-workaround.nix {
  inherit pkgs hostname;
  chromePackage = chromeWithMachineVideoDecoding;
}).chromeForMachine
