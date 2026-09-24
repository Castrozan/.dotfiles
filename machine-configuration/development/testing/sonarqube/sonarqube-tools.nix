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
  serverVersion = "1.26.0.4269";
  server = pkgs.fetchurl {
    url = "https://binaries.sonarsource.com/Distribution/sonarqube-mcp-server/sonarqube-mcp-server-${serverVersion}.jar";
    hash = "sha256-9cshS5SKHip7L4xk612kGFq1jIZM89evtKi7tn+3ZlA=";
  };
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
  mcp = pkgs.writeShellApplication {
    name = "sonarqube-mcp";
    runtimeInputs = [ pkgs.coreutils ];
    runtimeEnv = {
      SONARQUBE_ORG = "castrozan-oss";
      SONARQUBE_URL = "https://sonarcloud.io";
      SONARQUBE_TOOLSETS = "issues,projects,quality-gates,rules,duplications,measures,coverage,languages";
      SONARQUBE_READ_ONLY = "true";
      SONARQUBE_LOG_TO_FILE_DISABLED = "true";
    };
    text = ''
      SONARQUBE_TOKEN="$(cat "''${SONARQUBE_TOKEN_FILE:-$HOME/.secrets/sonarqube-token}")"
      export SONARQUBE_TOKEN
      export STORAGE_PATH="''${XDG_CACHE_HOME:-$HOME/.cache}/sonarqube-mcp"
      mkdir -p "$STORAGE_PATH"
      exec ${pkgs.jdk21_headless}/bin/java -Xmx384m -jar ${server} "$@"
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
