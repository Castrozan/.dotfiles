{
  pkgs,
  probes,
  ...
}:
let
  probeDefinitions = pkgs.writeText "health-check-probes.json" (
    builtins.toJSON (
      map (probe: {
        inherit (probe)
          category
          name
          probe
          applicableWhen
          ;
      }) probes
    )
  );

  healthCheckSource = pkgs.writeText "health-check-source.py" (
    builtins.readFile ./scripts/health_check.py
  );
in
pkgs.writeShellApplication {
  name = "health-check";
  runtimeInputs = with pkgs; [ coreutils ];
  text = ''
    exec ${pkgs.python312}/bin/python3 ${healthCheckSource} ${probeDefinitions} "$@"
  '';
}
