{
  pkgs,
  nodejs,
}:
let
  version = "1.2.0";
  npmTarball = pkgs.fetchurl {
    url = "https://registry.npmjs.org/chrome-devtools-mcp/-/chrome-devtools-mcp-${version}.tgz";
    hash = "sha256-r2qGlCRLSzDbSAM8sOClDBO7cIZkSEcJn571zHYgigU=";
  };
in
pkgs.stdenv.mkDerivation {
  pname = "chrome-devtools-mcp";
  inherit version;
  src = npmTarball;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    bundleRoot="$out/lib/chrome-devtools-mcp"
    mkdir -p "$bundleRoot"
    cp -R . "$bundleRoot/"

    makeWrapper ${nodejs}/bin/node "$out/bin/chrome-devtools-mcp" \
      --add-flags "$bundleRoot/build/src/bin/chrome-devtools-mcp.js"

    runHook postInstall
  '';

  meta = {
    description = "Pristine pinned chrome-devtools-mcp (no in-place patches; self-bundled, zero npm dependencies)";
    homepage = "https://github.com/ChromeDevTools/chrome-devtools-mcp";
  };
}
