{ pkgs, ... }:
let
  mkHomeAssistantPythonScript =
    name: file:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
    in
    pkgs.writeShellScriptBin name ''
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  home.packages = [
    (mkHomeAssistantPythonScript "ha-light" ./scripts/home_assistant_light_control.py)
    (mkHomeAssistantPythonScript "ha-ac" ./scripts/home_assistant_air_conditioner_control.py)
    (mkHomeAssistantPythonScript "ha-light-scene-cycle" ./scripts/home_assistant_light_scene_cycle.py)
    (mkHomeAssistantPythonScript "ha-ac-toggle" ./scripts/home_assistant_air_conditioner_toggle.py)
  ];
}
