{ pkgs }:
let
  packageVersion = "0.19.0";
  packageSource = pkgs.fetchzip {
    url = "https://registry.npmjs.org/chrome-devtools-mcp/-/chrome-devtools-mcp-${packageVersion}.tgz";
    hash = "sha256-qPm7WYpNjcvPC6PrKWehVKi5R0NwM/KPjPbF01jvUAc=";
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
      --add-flags "$out/lib/chrome-devtools-mcp/build/src/index.js"
    runHook postInstall
  '';
}
