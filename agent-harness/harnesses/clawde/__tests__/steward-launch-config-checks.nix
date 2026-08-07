{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };
  inherit (fixtures) bothHarnessModules parseDeployedJson;

  stewardLaunchConfig =
    parseDeployedJson
      (helpers.homeManagerTestConfiguration (bothHarnessModules ++ [ ../agents/steward.nix ]))
      .home.file."clawde/launch-config/steward.json".text;
in
{
  clawde-the-heartbeat-driver-carries-its-own-module-search-path =
    mkEvalCheck "clawde-the-heartbeat-driver-carries-its-own-module-search-path"
      (builtins.any (
        argument: pkgs.lib.hasPrefix "PYTHONPATH=" argument
      ) stewardLaunchConfig.heartbeat_driver_argv)
      "a rebuild regenerates this argv with the new generation's driver script while the supervisor that spawns it keeps the PYTHONPATH it launched with, so a driver relying on the inherited one dies on ModuleNotFoundError the moment a running agent restarts its session, and the watchdog then restart-loops the agent on a widening backoff until the whole supervisor is respawned";

  clawde-the-steward-can-fall-off-a-harness-that-stops-producing-turns =
    mkEvalCheck "clawde-the-steward-can-fall-off-a-harness-that-stops-producing-turns"
      (
        builtins.filter (
          harnessName: harnessName != stewardLaunchConfig.declared_harness
        ) stewardLaunchConfig.harness_fallback_chain != [ ]
      )
      "the steward is the one agent nothing else watches, so a fallback chain holding nothing but its own declared harness leaves it parked and silent the next time its provider refuses work: it holds a live process, an idle pane and a firing heartbeat throughout, which is how it once sat out three days of a weekly usage limit while every liveness probe reported it healthy";

  clawde-every-steward-fallback-is-a-harness-it-can-actually-reach =
    mkEvalCheck "clawde-every-steward-fallback-is-a-harness-it-can-actually-reach"
      (builtins.all (
        harnessName:
        builtins.elem harnessName (builtins.attrNames stewardLaunchConfig.harness_launch_commands)
      ) stewardLaunchConfig.harness_fallback_chain)
      "the runtime skips a fallback the agent is not eligible for, so a chain naming a harness this machine never materialized a launch command for silently shortens to nothing and the failover reads as configured while doing nothing";
}
