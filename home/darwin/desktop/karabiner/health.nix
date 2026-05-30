{ healthCheckLib, ... }:
{
  healthCheck.probes = [
    (healthCheckLib.mkAppProbe {
      name = "Karabiner-Elements.app";
      bundle = "Karabiner-Elements";
    })
    (healthCheckLib.mkProcessProbe {
      name = "karabiner_console_user_server";
      pattern = "karabiner_console_user_server";
    })
  ];
}
