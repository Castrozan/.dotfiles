{ helpers, ... }:
let
  configuration = helpers.homeManagerTestConfiguration [ ../devenv-container-home-manager.nix ];
  policy = builtins.fromJSON (
    builtins.unsafeDiscardStringContext configuration.xdg.configFile."devenv-container/policy.json".text
  );
in
helpers.mkEvalCheckGroup "domain-dev-devenv-container" {
  memory-budget = {
    assertion = policy.container_memory_bytes < policy.virtual_machine_memory_gib * 1024 * 1024 * 1024;
    message = "The development VM must retain memory outside project containers";
  };
  cpu-budget = {
    assertion = policy.container_cpus <= policy.virtual_machine_cpus;
    message = "Project CPU quotas must fit the development VM budget";
  };
  cleanup = {
    assertion =
      configuration.systemd.user.timers.devenv-container-cleanup.Timer.OnUnitActiveSec == "1min";
    message = "Abandoned environments must be collected without depending on the agent";
  };
  command-deadline = {
    assertion = policy.command_timeout_seconds <= policy.session_timeout_seconds;
    message = "Finite commands must fit inside the environment lifespan";
  };
}
