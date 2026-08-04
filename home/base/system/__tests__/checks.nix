{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../../../linux/system/lid-switch-ignore.nix
    ../../../linux/system/oom-protection.nix
    ../stale-symlink-cleanup.nix
  ];

  hasActivation = name: builtins.hasAttr name cfg.home.activation;

  healthCheckLib = import ../health-check/lib.nix { inherit lib; };

  buildHealthCheck =
    probes:
    import ../health-check/script.nix {
      inherit pkgs lib probes;
    };

  dormantComponentReason = "weekday-only agent, weekend";

  healthCheckWithDormantProbe = buildHealthCheck [
    (healthCheckLib.mkCommandProbe {
      name = "dormant component";
      command = "false";
      applicableWhen = "echo ${lib.escapeShellArg dormantComponentReason}; exit 1";
    })
    (healthCheckLib.mkCommandProbe {
      name = "live component";
      command = "true";
    })
  ];

  healthCheckWithApplicableFailure = buildHealthCheck [
    (healthCheckLib.mkCommandProbe {
      name = "broken component";
      command = "false";
      applicableWhen = "exit 0";
    })
  ];

  healthCheckWithSlowProbe = buildHealthCheck [
    (healthCheckLib.mkCommandProbe {
      name = "slow component";
      command = "sleep 5; true";
    })
  ];

  healthCheckWithSlowApplicabilityCheck = buildHealthCheck [
    (healthCheckLib.mkCommandProbe {
      name = "component behind a hung applicability check";
      command = "true";
      applicableWhen = "sleep 5; exit 1";
    })
  ];
in
{
  domain-system-oom-protection =
    mkEvalCheck "domain-system-oom-protection" (hasActivation "setupOomProtection")
      "oom protection activation should exist";

  domain-system-lid-switch =
    mkEvalCheck "domain-system-lid-switch" (hasActivation "setupLidSwitchIgnore")
      "lid switch ignore activation should exist";

  domain-system-stale-symlink-cleanup =
    mkEvalCheck "domain-system-stale-symlink-cleanup" (hasActivation "removeStaleNixStoreSymlinks")
      "stale nix store symlink cleanup activation should exist";

  domain-system-health-check-skips-dormant-probe =
    pkgs.runCommandLocal "check-domain-system-health-check-skips-dormant-probe" { }
      ''
        ${healthCheckWithDormantProbe}/bin/health-check >output.txt
        grep -qF '1/1 passed (0 failed, 1 skipped)' output.txt
        grep -qF ${lib.escapeShellArg dormantComponentReason} output.txt
        touch $out
      '';

  domain-system-health-check-reports-skip-in-json =
    pkgs.runCommandLocal "check-domain-system-health-check-reports-skip-in-json" { }
      ''
        ${healthCheckWithDormantProbe}/bin/health-check --json >output.json
        grep -qF '"name":"dormant component","status":"skip","reason":"${dormantComponentReason}"' output.json
        grep -qF '"name":"live component","status":"pass"' output.json
        touch $out
      '';

  domain-system-health-check-still-fails-an-applicable-probe =
    pkgs.runCommandLocal "check-domain-system-health-check-still-fails-an-applicable-probe" { }
      ''
        exitCode=0
        ${healthCheckWithApplicableFailure}/bin/health-check >output.txt || exitCode=$?
        test "$exitCode" -eq 1
        grep -qF '0/1 passed (1 failed)' output.txt
        touch $out
      '';

  domain-system-health-check-fails-a-probe-that-exceeds-its-timeout =
    pkgs.runCommandLocal "check-domain-system-health-check-fails-a-probe-that-exceeds-its-timeout" { }
      ''
        exitCode=0
        HEALTH_CHECK_PROBE_TIMEOUT_SECONDS=1 \
          ${healthCheckWithSlowProbe}/bin/health-check >output.txt || exitCode=$?
        test "$exitCode" -eq 1
        grep -qF '0/1 passed (1 failed)' output.txt
        grep -qF 'timed out after 1s' output.txt
        touch $out
      '';

  domain-system-health-check-fails-rather-than-skips-a-hung-applicability-check =
    pkgs.runCommandLocal
      "check-domain-system-health-check-fails-rather-than-skips-a-hung-applicability-check"
      { }
      ''
        exitCode=0
        HEALTH_CHECK_PROBE_TIMEOUT_SECONDS=1 \
          ${healthCheckWithSlowApplicabilityCheck}/bin/health-check >output.txt || exitCode=$?
        test "$exitCode" -eq 1
        grep -qF '0/1 passed (1 failed)' output.txt
        grep -qF 'applicability check timed out after 1s' output.txt
        touch $out
      '';
}
