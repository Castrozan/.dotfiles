{ pkgs, inputs }:
let
  darwinRelease = {
    version = "0.24.0";
    hash = "sha256-7wA/Y/kRRYWyObJaPVm6I0aULHrUOdtwokslEwZ0NYc=";
  };

  darwinApplicationBundle = pkgs.stdenvNoCC.mkDerivation {
    pname = "delta-app";
    inherit (darwinRelease) version;
    src = pkgs.fetchurl {
      url = "https://releases.delta.dev/releases/stable/${darwinRelease.version}/macos/aarch64/Delta.app.zip";
      inherit (darwinRelease) hash;
    };
    nativeBuildInputs = [ pkgs.unzip ];
    sourceRoot = ".";
    dontConfigure = true;
    dontBuild = true;
    dontFixup = true;
    installPhase = ''
      mkdir -p "$out/Applications"
      cp -a Delta.app "$out/Applications/"
    '';
    meta.platforms = [ "aarch64-darwin" ];
  };
in
if pkgs.stdenv.hostPlatform.isDarwin then
  {
    package = darwinApplicationBundle;
    commandLine = "${darwinApplicationBundle}/Applications/Delta.app/Contents/MacOS/delta";
  }
else
  let
    linuxPackage = inputs.delta-nix.packages.${pkgs.stdenv.hostPlatform.system}.delta;
  in
  {
    package = linuxPackage;
    commandLine = "${linuxPackage}/bin/delta";
  }
