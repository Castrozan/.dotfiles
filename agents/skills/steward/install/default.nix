{ pkgs }:
let
  python = pkgs.python312;

  stewardStatusSource = pkgs.writeText "steward-status.py" (
    builtins.readFile ../scripts/steward-status.py
  );

  stewardMessageSource = pkgs.writeText "steward-msg.py" (
    builtins.readFile ../scripts/steward-msg.py
  );

  stewardStatus = pkgs.writeShellScriptBin "steward-status" ''
    set -euo pipefail
    export PATH="${pkgs.git}/bin:${pkgs.coreutils}/bin:''${PATH:+$PATH}"
    exec ${python}/bin/python3 ${stewardStatusSource} "$@"
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
