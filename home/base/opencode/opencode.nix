{ pkgs, ... }:
let
  fetchPrebuiltBinary = import ../../../lib/fetch-prebuilt-binary.nix { inherit pkgs; };

  version = "1.17.7";

  opencodeUpstreamReleaseDescriptorBySystem = {
    "x86_64-linux" = {
      releaseAssetName = "opencode-linux-x64.tar.gz";
      sha256 = "sha256-YP5aktya9k7AeTSP7d4X4S2mqGfv5+g1O+gDhIBgeSQ=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      releaseAssetName = "opencode-darwin-arm64.zip";
      sha256 = "sha256-emOutaFbKdomgawrjHTUyzpk+hO2EZijx9x3EkPCOXI=";
      buildInputs = [ ];
    };
  };

  currentHostSystem = opencodeUpstreamReleaseDescriptorBySystem.${pkgs.stdenv.hostPlatform.system};

  opencode = fetchPrebuiltBinary {
    pname = "opencode";
    inherit version;
    url = "https://github.com/anomalyco/opencode/releases/download/v${version}/${currentHostSystem.releaseAssetName}";
    inherit (currentHostSystem) sha256 buildInputs;
    binaryName = "opencode";
    archiveBinaryPath = "opencode";
  };
in
{
  home.packages = [ opencode ];
  home.file.".local/bin/opencode".source = "${opencode}/bin/opencode";
}
