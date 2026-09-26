{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };
  version = "1.18.32";
  releases = {
    "x86_64-linux" = {
      releaseAssetName = "opencode-linux-x64.tar.gz";
      sha256 = "sha256-MEbgQE/cYPuAMH56R4JLoHR3NkF4pNCbqoVISW3W1Ds=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      releaseAssetName = "opencode-darwin-arm64.zip";
      sha256 = "sha256-+mQ/k0AcE1CNjVE3gOVM6cwBID1QERS+m4jWJAi4EB8=";
      buildInputs = [ ];
    };
  };
  release = releases.${pkgs.stdenv.hostPlatform.system};
in
fetchPrebuiltBinary {
  pname = "opencode";
  inherit version;
  url = "https://github.com/anomalyco/opencode/releases/download/v${version}/${release.releaseAssetName}";
  inherit (release) sha256 buildInputs;
  binaryName = "opencode";
  archiveBinaryPath = "opencode";
}
