{ pkgs }:
let
  version = "4.1.2";
  appBundleZipName = "fish-${version}.app.zip";
  upstreamReleaseUrl = "https://github.com/fish-shell/fish-shell/releases/download/${version}/${appBundleZipName}";
  appBundleZipHash = "sha256-cTCvVrSjLQAhlZb2dDXXi6jbWaxxh/MQQGcRlhrnqvU=";
  unpackedRelativePrefixPathInsideAppBundle = "Contents/Resources/base/usr/local";
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "fish";
  inherit version;

  src = pkgs.fetchurl {
    url = upstreamReleaseUrl;
    hash = appBundleZipHash;
  };

  nativeBuildInputs = [ pkgs.unzip ];

  dontStrip = true;
  dontFixup = true;

  unpackPhase = ''
    runHook preUnpack
    unzip -q $src
    runHook postUnpack
  '';

  sourceRoot = "fish-${version}.app";

  installPhase = ''
    runHook preInstall
    mkdir -p $out
    cp -R ${unpackedRelativePrefixPathInsideAppBundle}/. $out/
    runHook postInstall
  '';

  meta = {
    description = "fish ${version} prebuilt darwin binary from upstream releases, preserves Apple code signature so macOS 26.1 (Tahoe) does not SIGKILL at exec";
    homepage = "https://fishshell.com/";
    license = pkgs.lib.licenses.gpl2Only;
    platforms = [
      "aarch64-darwin"
      "x86_64-darwin"
    ];
    mainProgram = "fish";
  };
}
