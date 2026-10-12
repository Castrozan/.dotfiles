{
  latest,
  lib,
  inputs,
  version,
  releasePackage,
}:
let
  toolchainPackages = latest.extend inputs.herdr.inputs.rust-overlay.overlays.default;
  rustToolchain = toolchainPackages.rust-bin.stable."1.95.0".minimal;
  rustPlatform = latest.makeRustPlatform {
    cargo = rustToolchain;
    rustc = rustToolchain;
  };
  v8ArchiveHashes = {
    x86_64-linux = "sha256-WGn9twcbHyHyAKl86X0gElh34PMc2ALtmd4sU/SIsGw=";
    aarch64-darwin = "sha256-zNj4FIW4IsWxiuun+d65KaM4LYasZzu/DzZvBod+axA=";
  };
in
rustPlatform.buildRustPackage {
  pname = "codex";
  inherit version;
  src = latest.fetchFromGitHub {
    owner = "openai";
    repo = "codex";
    tag = "rust-v${version}";
    hash = "sha256-YG/9hFOCl4cMYzjaH/3gBid4osxcrvCYQUDDzdbIygo=";
  };
  sourceRoot = "source/codex-rs";
  cargoHash = "sha256-UTu+ws1DqL375C+1jaVI9HBqDHnTuAQr7/h1rSzsEzg=";
  patches = [
    ./patches/compact-status-line.patch
    ./patches/compact-status-line-tests.patch
  ];
  cargoBuildFlags = [
    "--package"
    "codex-cli"
    "--bin"
    "codex"
  ];
  cargoTestFlags = [
    "--package"
    "codex-tui"
    "--lib"
    "bottom_pane::status_line_"
  ];
  nativeBuildInputs = with latest; [
    pkg-config
    clang
    cmake
    gitMinimal
  ];
  buildInputs = [ latest.openssl ] ++ lib.optional latest.stdenv.hostPlatform.isLinux latest.libcap;
  env = {
    LIBCLANG_PATH = "${lib.getLib latest.libclang}/lib";
    RUSTY_V8_ARCHIVE = latest.fetchurl {
      url = "https://github.com/denoland/rusty_v8/releases/download/v150.4.0/librusty_v8_release_${latest.stdenv.hostPlatform.rust.rustcTarget}.a.gz";
      hash = v8ArchiveHashes.${latest.stdenv.hostPlatform.system};
    };
  };
  preBuild = "export NIX_BUILD_CORES=2";
  postPatch = ''
    substituteInPlace Cargo.toml \
      --replace-fail 'lto = "thin"' 'lto = false' \
      --replace-fail 'debug = "line-tables-only"' 'debug = false' \
      --replace-fail 'codegen-units = 4' 'codegen-units = 16'
  '';
  postInstall = ''
    cp -R ${releasePackage}/{codex-resources,codex-path,env-vars,codex-package.json} "$out/"
    ln -s ${releasePackage}/bin/codex-code-mode-host "$out/bin/codex-code-mode-host"
  '';
  doCheck = true;
  doInstallCheck = true;
  installCheckPhase = ''
    "$out/bin/codex" --version
    "$out/bin/codex-code-mode-host" --help >/dev/null
  '';
  meta = {
    description = "Codex with a bounded status line";
    mainProgram = "codex";
    license = lib.licenses.asl20;
    platforms = builtins.attrNames v8ArchiveHashes;
  };
}
