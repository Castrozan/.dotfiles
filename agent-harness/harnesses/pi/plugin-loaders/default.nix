{ pkgs }:
let
  packageLock = builtins.fromJSON (builtins.readFile ./package-lock.json);
  sdkModule = "node_modules/@earendil-works/pi-coding-agent";
  sdk = packageLock.packages.${sdkModule};
  sdkArchive = pkgs.fetchurl {
    url = sdk.resolved;
    hash = sdk.integrity;
  };
  sdkWithoutEmbeddedLock = pkgs.runCommand "pi-sdk-without-embedded-lock.tgz" { } ''
    tar -xzf ${sdkArchive}
    chmod -R u+w package
    rm package/npm-shrinkwrap.json
    tar -czf "$out" package
  '';
  buildPackageLock = packageLock // {
    packages = packageLock.packages // {
      ${sdkModule} = builtins.removeAttrs sdk [
        "integrity"
        "hasShrinkwrap"
      ];
    };
  };
in
pkgs.importNpmLock.buildNodeModules {
  npmRoot = ./.;
  packageLock = buildPackageLock;
  nodejs = pkgs.nodejs_22;
  derivationArgs.npmDeps = pkgs.importNpmLock {
    npmRoot = ./.;
    packageLock = buildPackageLock;
    packageSourceOverrides.${sdkModule} = sdkWithoutEmbeddedLock;
  };
  derivationArgs.doInstallCheck = true;
  derivationArgs.installCheckPhase = ''
    test -f "$out/node_modules/@earendil-works/pi-coding-agent/dist/index.js"
    test -f "$out/node_modules/pi-agent-plugins/extensions/index.ts"
    test -f "$out/node_modules/pi-mcp-adapter/index.ts"
    node "$out/node_modules/@earendil-works/pi-coding-agent/dist/cli.js" --version
    node ${./check-loaders.mjs} "$out/node_modules"
  '';
}
