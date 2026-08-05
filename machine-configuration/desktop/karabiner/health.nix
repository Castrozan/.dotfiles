{ healthCheckLib, ... }:
{
  healthCheck.probes = [
    (healthCheckLib.mkProcessProbe {
      name = "karabiner_console_user_server";
      pattern = "karabiner_console_user_server";
    })
  ];
}
