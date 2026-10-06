{
  inputs,
  pkgs,
  lib,
}:
let
  upstreamPayload = inputs.clawde.stewardPayloadPath;
  upstreamPackages = (import (upstreamPayload + "/install/default.nix") { inherit pkgs; }).packages;
  forgePackage =
    (import ../../../../agent-instructions/skills/development/forge/install { inherit pkgs; }).packages;
  statusSource = pkgs.runCommand "steward-forge-status-source" { } ''
    mkdir -p $out
    cp ${upstreamPayload}/scripts/steward-status.py $out/steward-status.py
    cp ${upstreamPayload}/scripts/repository_status.py $out/repository_status.py
    cp ${upstreamPayload}/scripts/health_summary.py $out/health_summary.py
    cp ${upstreamPayload}/scripts/submodule_status.py $out/submodule_status.py
    cp ${./continuous_integration_status.py} $out/continuous_integration_status.py
  '';
  status = pkgs.writeShellScriptBin "steward-status" ''
    export PATH="${
      lib.makeBinPath (
        forgePackage
        ++ [
          pkgs.git
          pkgs.gh
          pkgs.glab
          pkgs.coreutils
        ]
      )
    }:''${PATH:+:$PATH}"
    exec ${pkgs.python312}/bin/python3 ${statusSource}/steward-status.py "$@"
  '';
  heartbeat = pkgs.writeShellScriptBin "steward-heartbeat-probe" ''
    export STEWARD_STATUS_COMMAND="${status}/bin/steward-status"
    exec ${pkgs.python312}/bin/python3 ${upstreamPayload}/scripts/steward-heartbeat-probe.py "$@"
  '';
  otherPackages = builtins.filter (
    package:
    !(builtins.elem (lib.getName package) [
      "steward-status"
      "steward-heartbeat-probe"
    ])
  ) upstreamPackages;
in
{
  packages = otherPackages ++ [
    status
    heartbeat
  ];
  profilePackages = map lib.hiPrio [
    status
    heartbeat
  ];
}
