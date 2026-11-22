{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };
  version = "2.3.2";
  releases = {
    "x86_64-linux" = {
      platform = "linux-x64";
      sha256 = "sha256-hFRo41qlorV0lFoLlmdeZMYE9Sec7ZqnJFBo2MC29rs=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      platform = "darwin-arm64";
      sha256 = "sha256-gp+RF5pvQID1KNOmdWuH0umVPev7CgaKWb9HPS11Nak=";
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
