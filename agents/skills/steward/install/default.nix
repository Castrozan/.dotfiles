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

  stewardHeartbeatGate = pkgs.writeShellScriptBin "steward-heartbeat-gate" ''
    set -euo pipefail
    ${stewardStatus}/bin/steward-status \
      | ${python}/bin/python3 -c 'import json, sys; sys.exit(0 if json.load(sys.stdin).get("attention_required") else 1)'
  '';
in
{
  packages = [
    stewardStatus
    stewardMessage
    stewardHeartbeatGate
  ];
}
