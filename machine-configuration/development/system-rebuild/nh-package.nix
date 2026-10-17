{ pkgs }:
let
  fetchPrebuiltBinary = import ../../../repository/nix-library/fetch-prebuilt-binary.nix {
    inherit pkgs;
  };
  version = "4.4.2";
  releaseHashes = {
    aarch64-darwin = "sha256:7749070a4281a4ea5fc6b4f809f18de627e3d3576ba0a0e1d092336e141ff3b1";
    aarch64-linux = "sha256:0468b74740f3c2f394acf2f87a4914df438c40e8c281b8207f49248e6cc992b3";
    x86_64-linux = "sha256:cfa59e55fda714ce4227c498d760f6fda2fb9075f6fb6cd99f58444518ea5614";
  };
  unwrapped = fetchPrebuiltBinary {
    pname = "nh";
    inherit version;
    url = "https://github.com/nix-community/nh/releases/download/v${version}/nh-${pkgs.stdenv.hostPlatform.system}";
    sha256 = releaseHashes.${pkgs.stdenv.hostPlatform.system};
    preserveCodeSignature = pkgs.stdenv.hostPlatform.isDarwin;
    meta = {
      description = "Nix helper with package search and generation inspection";
      homepage = "https://github.com/nix-community/nh";
      license = pkgs.lib.licenses.eupl12;
      mainProgram = "nh";
      platforms = builtins.attrNames releaseHashes;
    };
  };
  guardScript = pkgs.writeShellScript "nh-guard" (builtins.readFile ./scripts/nh-guard);
in
pkgs.symlinkJoin {
  inherit (unwrapped) name meta;
  inherit version;
  paths = [ unwrapped ];
  nativeBuildInputs = [ pkgs.makeBinaryWrapper ];
  postBuild = ''
    rm $out/bin/nh
    makeWrapper ${guardScript} $out/bin/nh \
      --set REAL_NH ${unwrapped}/bin/nh \
      --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.nix-output-monitor ]}
  '';
}
