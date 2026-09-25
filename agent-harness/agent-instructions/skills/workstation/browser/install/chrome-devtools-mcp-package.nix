{
  pkgs,
  nodejs,
}:
let
  version = "1.10.1";
  npmTarball = pkgs.fetchurl {
    url = "https://registry.npmjs.org/chrome-devtools-mcp/-/chrome-devtools-mcp-${version}.tgz";
    hash = "sha256-ASy89ugy1PZwna0MIde+8XCJ6Ure6c8zF50V6gqa3ys=";
  };
in
pkgs.stdenv.mkDerivation {
  pname = "chrome-devtools-mcp";
  inherit version;
  src = npmTarball;

  patches = [
    ./chrome-devtools-mcp-patches/lazy-devtools-universe.patch
    ./chrome-devtools-mcp-patches/nonblocking-page-titles.patch
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontConfigure = true;
  dontBuild = true;

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck
    CHROME_DEVTOOLS_MCP_PACKAGE="$out/lib/chrome-devtools-mcp" \
      ${nodejs}/bin/node --test \
        ${./__tests__/resource-retention.test.mjs} \
        ${./__tests__/devtools-lifecycle.test.mjs}
    runHook postInstallCheck
  '';

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
    description = "Chrome DevTools MCP with upstream retention fixes, on-demand DevTools sessions, and nonblocking page titles";
    homepage = "https://github.com/ChromeDevTools/chrome-devtools-mcp";
  };
}
