{ inputs, system }:
inputs.hermes.packages.${system}.minimal.override {
  extraDependencyGroups = [
    "anthropic"
    "messaging"
  ];
}
