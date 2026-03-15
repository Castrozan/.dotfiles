{ pkgs }:
let
  packageVersion = "0.20.0";
  packageSource = pkgs.fetchzip {
    url = "https://registry.npmjs.org/chrome-devtools-mcp/-/chrome-devtools-mcp-${packageVersion}.tgz";
    hash = "sha256-tbi5cmrF1m3uI2fgHg5GgbmKhPaamn2dCeKwS8gRe6w=";
  };
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "chrome-devtools-mcp";
  version = packageVersion;
  src = packageSource;
  nativeBuildInputs = [ pkgs.makeWrapper ];
  installPhase = ''
    runHook preInstall
    mkdir -p "$out/bin" "$out/lib/chrome-devtools-mcp"
    cp -R ./* "$out/lib/chrome-devtools-mcp/"
    makeWrapper ${pkgs.nodejs_22}/bin/node "$out/bin/chrome-devtools-mcp" \
      --add-flags "$out/lib/chrome-devtools-mcp/build/src/index.js" \
      --set NODE_PATH "$out/lib/chrome-devtools-mcp/node_modules"
    runHook postInstall
  '';
}
