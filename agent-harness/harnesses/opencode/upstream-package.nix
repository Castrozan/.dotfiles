{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };
  version = "2.4.2";
  releases = {
    "x86_64-linux" = {
      platform = "linux-x64";
      sha256 = "sha256-mdKIy1xoQRYiy9WlYpr7jwcRDNCnSNfN1+s0sIz1b1o=";
      buildInputs = [ ];
    };
    "aarch64-darwin" = {
      platform = "darwin-arm64";
      sha256 = "sha256-PPoEu6ktsxRk1JMJp74r48kLMrSqV5KlVrX6GPI4QYo=";
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
