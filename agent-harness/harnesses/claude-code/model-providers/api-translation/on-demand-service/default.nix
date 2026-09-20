{ pkgs }:
let
  onDemandLifecycleSource = pkgs.runCommandLocal "on-demand-proxy-lifecycle" { } ''
    mkdir -p $out
    cp ${./scripts/on_demand_proxy_lifecycle.py} $out/on_demand_proxy_lifecycle.py
    cp ${./scripts/holder_registry.py} $out/holder_registry.py
    cp ${./scripts/service_commands.py} $out/service_commands.py
  '';
in
{
  serviceControllerName = if pkgs.stdenv.hostPlatform.isDarwin then "launchd" else "systemd";

  serviceLabelFor =
    { launchdAgentLabel, systemdServiceName }:
    if pkgs.stdenv.hostPlatform.isDarwin then launchdAgentLabel else systemdServiceName;

  lifecycleProgramArguments = [
    "${pkgs.python312}/bin/python3"
    "${onDemandLifecycleSource}/on_demand_proxy_lifecycle.py"
  ];
}
