{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };
  version = "2.2.6";
  releases = {
    "x86_64-linux" = {
      platform = "linux-x64";
      sha256 = "sha256-381p8dURrhDtYmdotB2EuBAMxKpkzstp2ji6einTNVE=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      platform = "darwin-arm64";
      sha256 = "sha256-YT67dN2O/3Z7udRCo3tAxNmUa6J/FTiYUGihuWeBN6M=";
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
