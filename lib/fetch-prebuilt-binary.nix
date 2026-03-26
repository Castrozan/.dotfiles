{ pkgs }:
{
  pname,
  version,
  url,
  sha256,
  binaryName ? pname,
  buildInputs ? [ ],
  nativeBuildInputs ? [ ],
  archiveBinaryPath ? null,
  meta ? { },
}:
let
  urlEndsWithAny = suffixes: builtins.any (suffix: pkgs.lib.hasSuffix suffix url) suffixes;

  isDebArchive = pkgs.lib.hasSuffix ".deb" url;

  isTarballArchive = urlEndsWithAny [
    ".tar.gz"
    ".tgz"
    ".tar.zst"
  ];

  isZipArchive = pkgs.lib.hasSuffix ".zip" url;

  isArchive = isDebArchive || isTarballArchive || isZipArchive;

  isTarZstd = pkgs.lib.hasSuffix ".tar.zst" url;

  archiveSpecificNativeBuildInputs =
    if isDebArchive then
      [ pkgs.dpkg ]
    else if isTarZstd then
      [
        pkgs.zstd
        pkgs.gnutar
      ]
    else if isZipArchive then
      [ pkgs.unzip ]
    else
      [ ];

  resolvedArchiveBinaryPath =
    if archiveBinaryPath != null then
      archiveBinaryPath
    else if isDebArchive then
      "usr/bin/${binaryName}"
    else
      binaryName;

  unpackPhaseForArchiveType =
    if isDebArchive then
      "dpkg -x $src ."
    else if isTarballArchive then
      "tar -xf $src"
    else if isZipArchive then
      "unzip $src"
    else
      "";
in
pkgs.stdenv.mkDerivation {
  inherit pname version meta;

  src = pkgs.fetchurl { inherit url sha256; };

  nativeBuildInputs = [
    pkgs.autoPatchelfHook
  ]
  ++ archiveSpecificNativeBuildInputs
  ++ nativeBuildInputs;
  buildInputs = [ pkgs.stdenv.cc.cc.lib ] ++ buildInputs;

  dontUnpack = !isArchive;
  dontStrip = true;

  sourceRoot = if isTarballArchive || isZipArchive then "." else null;

  unpackPhase = if isDebArchive then unpackPhaseForArchiveType else null;

  installPhase =
    if isArchive then
      ''
        install -Dm755 ${resolvedArchiveBinaryPath} $out/bin/${binaryName}
      ''
    else
      ''
        install -Dm755 $src $out/bin/${binaryName}
      '';
}
