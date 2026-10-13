{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };
  version = "2.0.28";
  releases = {
    "x86_64-linux" = {
      platform = "linux-x64";
      sha256 = "sha256-dvhQW6r1aWXtKPMFt0xSa1TszRj+eMgWIaQJDMAmyfk=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      platform = "darwin-arm64";
      sha256 = "sha256-PPIpzDrdHxyqd+V6J8mDTYF52/u2lPnzboat1rkrUSE=";
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
