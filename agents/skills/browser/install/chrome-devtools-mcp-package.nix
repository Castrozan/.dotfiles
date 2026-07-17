{
  pkgs,
  nodejs,
}:
let
  version = "1.6.0";
  npmTarball = pkgs.fetchurl {
    url = "https://registry.npmjs.org/chrome-devtools-mcp/-/chrome-devtools-mcp-${version}.tgz";
    hash = "sha256-HmMsLZcUtPgrTPq077nOV1CFx1/+XpdyODEprwEsnIQ=";
  };
in
pkgs.stdenv.mkDerivation {
  pname = "chrome-devtools-mcp";
  inherit version;
  src = npmTarball;

  patches = [ ./chrome-devtools-mcp-patches/parallelize-list-pages-title-fetch.patch ];

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
    description = "Pinned chrome-devtools-mcp, self-bundled with zero npm dependencies, carrying one upstream-bug patch that parallelizes the list_pages title fetch so it does not stall for a second per open tab against the consent-attached Chrome";
    homepage = "https://github.com/ChromeDevTools/chrome-devtools-mcp";
  };
}
