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

  healthCheckSources = pkgs.runCommand "health-check-python-sources" { } ''
    mkdir -p "$out/health_probes"
    cp ${./scripts/health_check.py} "$out/health_check.py"
    cp ${./scripts/health_probes/probe_execution.py} "$out/health_probes/probe_execution.py"
  '';
in
pkgs.writeShellApplication {
  name = "health-check";
  runtimeInputs = with pkgs; [ coreutils ];
  text = ''
    exec ${pkgs.python312}/bin/python3 ${healthCheckSources}/health_check.py ${probeDefinitions} "$@"
  '';
}
