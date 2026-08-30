{
  pkgs,
  nodejs,
}:
let
  sourceFiles = pkgs.lib.fileset.unions [
    ./node-provider-runtime/package.json
    ./node-provider-runtime/package-lock.json
    ./node-provider-runtime/provider-runtime.mjs
    ./node-provider-runtime/provider-adapters.mjs
    ./node-provider-runtime/provider-runners.mjs
    ./node-provider-runtime/provider-adapters.test.mjs
    ./node-provider-runtime/opencode-adapter.test.mjs
    ./node-provider-runtime/provider-load-smoke.test.mjs
    ./node-provider-runtime/provider-check-mode.test.mjs
  ];
in
pkgs.buildNpmPackage {
  pname = "agent-eval-node-provider-runtime";
  version = "0.0.0";
  inherit nodejs;

  src = pkgs.lib.fileset.toSource {
    root = ./node-provider-runtime;
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
