{ pkgs }:
let
  cli = import ./sonarqube-cli.nix { inherit pkgs; };
  policyFiles = [
    "cloud.json"
    "configure.py"
    "quality_gate.py"
    "quality_profiles.py"
    "sonar_api.py"
  ];
  policy = pkgs.runCommand "sonarqube-policy" { } ''
    mkdir -p "$out"
    ${pkgs.lib.concatMapStringsSep "\n" (
      name: ''cp ${../../../../repository/verification/quality/sonarqube + "/${name}"} "$out/${name}"''
    ) policyFiles}
  '';
in
{
  inherit cli;
  configure = pkgs.writeShellApplication {
    name = "sonar-configure";
    runtimeInputs = [ cli ];
    text = ''
      exec ${pkgs.python312}/bin/python ${policy}/configure.py "$@"
    '';
  };
  scanner = pkgs.writeShellApplication {
    name = "sonar-scanner";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      if [[ -z "''${SONAR_TOKEN:-}" ]]; then
        SONAR_TOKEN="$(cat "$HOME/.secrets/sonarqube-token")"
        export SONAR_TOKEN
      fi
      exec ${pkgs.sonar-scanner-cli}/bin/sonar-scanner "$@"
    '';
  };
}
