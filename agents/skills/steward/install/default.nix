{ pkgs }:
let
  python = pkgs.python312;

  stewardStatusSource = pkgs.runCommand "steward-status-source" { } ''
    mkdir -p $out
    cp ${../scripts/steward-status.py} $out/steward-status.py
    cp ${../scripts/continuous_integration_status.py} $out/continuous_integration_status.py
  '';

  stewardMessageSource = pkgs.writeText "steward-msg.py" (
    builtins.readFile ../scripts/steward-msg.py
  );

  stewardStatus = pkgs.writeShellScriptBin "steward-status" ''
    set -euo pipefail
    export PATH="${pkgs.git}/bin:${pkgs.gh}/bin:${pkgs.coreutils}/bin:''${PATH:+$PATH}"
    exec ${python}/bin/python3 ${stewardStatusSource}/steward-status.py "$@"
  '';

  stewardMessage = pkgs.writeShellScriptBin "steward-msg" ''
    set -euo pipefail
    export PATH="${pkgs.openssh}/bin:${pkgs.coreutils}/bin:''${PATH:+$PATH}"
    exec ${python}/bin/python3 ${stewardMessageSource} "$@"
  '';
in
{
  packages = [
    stewardStatus
    stewardMessage
  ];
}
