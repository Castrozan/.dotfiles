{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };
  version = "2.0.26";
  releases = {
    "x86_64-linux" = {
      platform = "linux-x64";
      sha256 = "sha256-ChFuAzoCgEdB1GRDN9ASvfWiSqwzo0wMllNNLVOWERk=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      platform = "darwin-arm64";
      sha256 = "sha256-e03cpeY9OKHSrd02gnCEPCOuugCWE9/Q4zhS05uGEHY=";
      buildInputs = [ ];
    };
  };
  release = releases.${pkgs.stdenv.hostPlatform.system};
in
fetchPrebuiltBinary {
  pname = "opencode";
  inherit version;
  url = "https://registry.npmjs.org/@opencode/cli-${release.platform}/-/cli-${release.platform}-${version}.tgz";
  inherit (release) sha256 buildInputs;
  binaryName = "opencode";
  archiveBinaryPath = "package/bin/opencode";
}
