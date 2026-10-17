{ pkgs, nodejs }:
pkgs.buildNpmPackage {
  pname = "opencli";
  version = "2.0.0";
  inherit nodejs;
  src = pkgs.lib.fileset.toSource {
    root = ./opencli;
    fileset = pkgs.lib.fileset.unions [
      ./opencli/package.json
      ./opencli/package-lock.json
    ];
  };
  npmDepsHash = "sha256-GZkkWNbFLFdHStpL4tx4g5338g+cGzE1Us+S8uIbiiY=";
  npmFlags = [ "--ignore-scripts" ];
  dontNpmBuild = true;
  dontNpmInstall = true;
  nativeBuildInputs = [ pkgs.makeWrapper ];

  OPENCLI_NODE = "${nodejs}/bin/node";
  installPhase = builtins.readFile ./scripts/opencli/install-opencli.sh;

  doInstallCheck = true;
  installCheckPhase = ''
    OPENCLI_PACKAGE_ROOT="$out/lib/opencli/node_modules/@jackwener/opencli" \
      ${nodejs}/bin/node --test ${./__tests__/opencli-bridge.test.mjs}
  '';

  meta = {
    description = "OpenCLI with authenticated, explicitly owned browser jobs";
    homepage = "https://github.com/jackwener/OpenCLI";
    license = pkgs.lib.licenses.asl20;
    mainProgram = "opencli";
  };
}
