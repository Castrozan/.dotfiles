{ healthCheckLib, ... }:
{
  healthCheck.probes = [
    (healthCheckLib.mkProcessProbe {
      name = "Karabiner-Console-User-Server";
      pattern = "Karabiner-Console-User-Server";
    })
  ];
}
