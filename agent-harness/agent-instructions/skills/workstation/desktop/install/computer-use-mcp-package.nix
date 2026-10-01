{ pkgs }:
let
  nodeArchitecture =
    {
      aarch64-darwin = "arm64";
      x86_64-darwin = "x64";
    }
    .${pkgs.stdenv.hostPlatform.system};
  protocolTestPython = pkgs.python312.withPackages (packages: [ packages.mcp ]);
in
pkgs.buildNpmPackage {
  pname = "desktop-computer-use";
  version = "7.4.0";
  nodejs = pkgs.nodejs_22;
  src = pkgs.lib.fileset.toSource {
    root = ./.;
    fileset = pkgs.lib.fileset.unions [
      ./package.json
      ./package-lock.json
    ];
  };
  npmDepsHash = "sha256-OKDngOdLcYOT3x6/usQgwK0CaNUqeTbDGZCXq9qQarw=";
  npmFlags = [
    "--ignore-scripts"
    "--omit=optional"
  ];
  dontNpmBuild = true;
  dontNpmInstall = true;
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall
    mkdir -p "$out/lib/desktop-computer-use"
    cp -R node_modules "$out/lib/desktop-computer-use/"
    find "$out/lib/desktop-computer-use/node_modules/@zavora-ai/computer-use-mcp" -maxdepth 1 -name '*.node' ! -name 'computer-use-napi.darwin-${nodeArchitecture}.node' -delete
    makeWrapper ${pkgs.nodejs_22}/bin/node "$out/bin/desktop-computer-use" \
      --add-flags "$out/lib/desktop-computer-use/node_modules/@zavora-ai/computer-use-mcp/dist/server.js" \
      --set COMPUTER_USE_PROFILE ax
    runHook postInstall
  '';

  doInstallCheck = true;
  installCheckPhase = ''
    ${pkgs.nodejs_22}/bin/node --input-type=module -e 'import {loadNative} from "'$out'/lib/desktop-computer-use/node_modules/@zavora-ai/computer-use-mcp/dist/native.js"; if (typeof loadNative().takeScreenshot !== "function") process.exit(1);'
    ${protocolTestPython}/bin/python3 ${./__tests__/mcp-smoke.py} "$out/bin/desktop-computer-use" doctor screenshot get_ui_tree left_click type
  '';

  meta = {
    description = "Native macOS desktop control over MCP";
    homepage = "https://github.com/zavora-ai/computer-use-mcp";
    license = pkgs.lib.licenses.mit;
    platforms = pkgs.lib.platforms.darwin;
    mainProgram = "desktop-computer-use";
  };
}
