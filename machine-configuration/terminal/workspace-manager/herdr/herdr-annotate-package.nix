{
  pkgs,
  lib,
  inputs,
}:
let
  toolchainPackages = pkgs.extend inputs.herdr.inputs.rust-overlay.overlays.default;
  rustToolchain = toolchainPackages.rust-bin.fromRustupToolchainFile (
    inputs.herdr + "/rust-toolchain.toml"
  );
  rustPlatform = pkgs.makeRustPlatform {
    cargo = rustToolchain;
    rustc = rustToolchain;
  };
  source = pkgs.fetchFromGitHub {
    owner = "plannotator";
    repo = "herdr-annotate";
    rev = "663b45a420f00882f7196bf893b341cddd37a530";
    hash = "sha256-MLHF21wqghawj3rk+UsyFdaGqIgVYXVG7UH2H+q0/lE=";
  };
  release = {
    aarch64-darwin = {
      target = "aarch64-apple-darwin";
      reviewHash = "sha256-qdpJ3WpE00lP7Q6DZsoymW7N9A4CcfztQQzsPIg5F10=";
    };
    x86_64-linux = {
      target = "x86_64-unknown-linux-gnu";
      reviewHash = "sha256-1U3GA8lfcQZ3vBPr5rJLLm6xDOdhV3r4qVoFAChit00=";
    };
  };
  platformRelease = release.${pkgs.stdenv.hostPlatform.system};
in
rustPlatform.buildRustPackage {
  pname = "herdr-annotate";
  version = "0.7.0";

  src = source;
  patches = [ ./patches/annotation-save-to-prompt.patch ];
  cargoRoot = "rust";
  buildAndTestSubdir = "rust";
  cargoLock.lockFile = source + "/rust/Cargo.lock";

  reviewRuntime = pkgs.fetchurl {
    url = "https://github.com/plannotator/plannotator-tui/releases/download/v0.9.4/plannotator-tui-${platformRelease.target}";
    hash = platformRelease.reviewHash;
  };

  nativeBuildInputs = [
    pkgs.makeWrapper
  ]
  ++ lib.optional pkgs.stdenv.hostPlatform.isLinux pkgs.autoPatchelfHook;
  buildInputs = lib.optional pkgs.stdenv.hostPlatform.isLinux pkgs.stdenv.cc.cc.lib;
  runtimePath = lib.makeBinPath (
    [ pkgs.bash ]
    ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
      pkgs.wl-clipboard
      pkgs.xclip
    ]
  );

  dontStrip = true;
  postInstall = builtins.readFile ./scripts/install-herdr-annotate.sh;

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck
    "$out/bin/herdr-annotate" --version
    "$out/bin/plannotator-tui" --version
    runHook postInstallCheck
  '';

  meta = {
    description = "Terminal annotations and document review for Herdr";
    homepage = "https://github.com/plannotator/herdr-annotate";
    license = lib.licenses.mit;
    platforms = builtins.attrNames release;
  };
}
