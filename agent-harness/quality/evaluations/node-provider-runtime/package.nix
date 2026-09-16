{
  pkgs,
  nodejs,
}:
let
  sourceFiles = pkgs.lib.fileset.unions [
    ./package.json
    ./package-lock.json
    ./provider-runtime.mjs
    ./provider-adapters.mjs
    ./provider-runners.mjs
    ./provider-usage.mjs
    ./provider-adapters.test.mjs
    ./provider-usage.test.mjs
    ./opencode-adapter.test.mjs
    ./provider-load-smoke.test.mjs
    ./provider-check-mode.test.mjs
  ];
in
pkgs.buildNpmPackage {
  pname = "agent-eval-node-provider-runtime";
  version = "0.0.0";
  inherit nodejs;

  src = pkgs.lib.fileset.toSource {
    root = ./.;
    fileset = sourceFiles;
  };

  npmDepsHash = "sha256-C7JMxnLavhFij7iHcZ9ikmQZgQTrGT8/CAgDSS3ck3I=";

  npmFlags = [
    "--ignore-scripts"
    "--omit=optional"
  ];
  dontNpmBuild = true;
  doCheck = true;

  checkPhase = ''
    node --test *.test.mjs
  '';

  meta = {
    description = "Packaged node subject runtime for agent evaluations: one stdin/result-file port that runs any of the three harness providers through their maintained SDKs";
    mainProgram = "agent-eval-provider";
  };
}
