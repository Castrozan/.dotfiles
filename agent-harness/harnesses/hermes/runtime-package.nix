{ inputs, system }:
let
  upstreamRuntime = inputs.hermes.packages.${system}.minimal;
  releaseWithStaleDarwinPnpmHash = "8fc0374447313e276f6b9a2764bfc750190c966a";
  needsDarwinPnpmHashCorrection =
    system == "aarch64-darwin" && inputs.hermes.rev == releaseWithStaleDarwinPnpmHash;

  callPackageWithCorrectedHermesPnpmHash =
    callPackage: package: arguments:
    callPackage package (
      if toString package == "${inputs.hermes}/nix/lib.nix" then
        arguments
        // {
          fetchPnpmDeps = callPackage (
            { fetchPnpmDeps }:
            dependencyArguments:
            fetchPnpmDeps (
              dependencyArguments
              // {
                hash = "sha256-W5V/4xsKZKolR2MQL5GN9GBa7844IPNmKVTTcLaZnvI=";
              }
            )
          ) { };
        }
      else
        arguments
    );
in
upstreamRuntime.override (
  upstreamArguments:
  {
    extraDependencyGroups = [
      "anthropic"
      "messaging"
    ];
  }
  // (
    if needsDarwinPnpmHashCorrection then
      {
        callPackage = callPackageWithCorrectedHermesPnpmHash upstreamArguments.callPackage;
      }
    else
      { }
  )
)
