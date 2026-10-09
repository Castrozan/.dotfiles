{
  imports = [
    ./local-lint/local-lint-home-manager.nix
    ../../../agent-harness/quality/evaluations/agent-evaluations-home-manager.nix
    ./benchmark-home-manager.nix
    ./nightly-deep-test-tiers-home-manager.nix
    ./testing-tools-home-manager.nix
  ];
}
