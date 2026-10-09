{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };
  version = "0.653.0";
  distributions = {
    aarch64-darwin = {
      platform = "aarch64-apple-darwin";
      hash = "sha256:8a213009e1d1cb2eeb1249cafa2b4953470f35764b3aefdee63349a915cfff0e";
    };
    x86_64-linux = {
      platform = "x86_64-unknown-linux-gnu";
      hash = "sha256:4836a710b7a3ba67d729121ba48fdfc4e183f414b88488c1bc598247974e39a6";
    };
    aarch64-linux = {
      platform = "aarch64-unknown-linux-gnu";
      hash = "sha256:008f938ddfcfac033689508aafd80697e327d140b03262b37b00419bda2c28f0";
    };
  };
  distribution = distributions.${pkgs.stdenv.hostPlatform.system};
in
fetchPrebuiltBinary {
  pname = "qlty";
  inherit version;
  url = "https://github.com/qltysh/qlty/releases/download/v${version}/qlty-${distribution.platform}.tar.xz";
  sha256 = distribution.hash;
  archiveBinaryPath = "qlty-${distribution.platform}/qlty";
  buildInputs = [
    pkgs.openssl
    pkgs.zlib
  ];
}
