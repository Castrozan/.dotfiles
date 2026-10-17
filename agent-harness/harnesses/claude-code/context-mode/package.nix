{ pkgs }:
pkgs.buildNpmPackage {
  pname = "context-mode";
  version = "1.0.169";
  nodejs = pkgs.nodejs_22;
  src = pkgs.lib.fileset.toSource {
    root = ./.;
    fileset = pkgs.lib.fileset.unions [
      ./package.json
      ./package-lock.json
    ];
  };
  npmDepsHash = "sha256-sS79O2OKef5SAH1ilq/+PYn8QFD8IJVMbAsUaSXCDDk=";
  npmFlags = [
    "--ignore-scripts"
    "--omit=optional"
  ];
  dontNpmBuild = true;
  dontNpmInstall = true;

  installPhase = ''
    runHook preInstall
    mkdir -p "$out/lib/context-mode"
    cp -R node_modules "$out/lib/context-mode/"
    runHook postInstall
  '';

  meta = {
    description = "Pinned Context Mode runtime and upstream Claude plugin";
    homepage = "https://github.com/mksglu/context-mode";
    license = pkgs.lib.licenses.elastic20;
    platforms = pkgs.lib.platforms.unix;
  };
}
