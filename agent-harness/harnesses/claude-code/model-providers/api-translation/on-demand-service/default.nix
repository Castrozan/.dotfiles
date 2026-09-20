{ pkgs }:
let
  onDemandLifecycleSource = pkgs.writeText "on-demand-proxy-lifecycle.py" (
    builtins.readFile ./scripts/on_demand_proxy_lifecycle.py
  );
in
{
  startCommandFor =
    { launchdAgentLabel, systemdServiceName }:
    if pkgs.stdenv.hostPlatform.isDarwin then
      [
        "launchctl"
        "kickstart"
        "gui/@CURRENT_USER_ID@/${launchdAgentLabel}"
      ]
    else
      [
        "systemctl"
        "--user"
        "start"
        systemdServiceName
      ];

  stopCommandFor =
    { launchdAgentLabel, systemdServiceName }:
    if pkgs.stdenv.hostPlatform.isDarwin then
      [
        "launchctl"
        "kill"
        "SIGTERM"
        "gui/@CURRENT_USER_ID@/${launchdAgentLabel}"
      ]
    else
      [
        "systemctl"
        "--user"
        "stop"
        systemdServiceName
      ];

  lifecycleProgramArguments = [
    "${pkgs.python312}/bin/python3"
    "${onDemandLifecycleSource}"
  ];
}
