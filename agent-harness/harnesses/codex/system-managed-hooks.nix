{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  ...
}:
let
  hooks = import ../../agent-instructions/rulesync/hooks {
    inherit
      pkgs
      lib
      hostname
      isDarwin
      ;
  };
  python = pkgs.python312.withPackages (packages: [ packages.tomli-w ]);
  codexManagedHooksRequirements = pkgs.runCommand "codex-managed-requirements.toml" { } ''
    ${python}/bin/python3 ${../../agent-instructions/rulesync/hooks/codex_requirements.py} \
      ${hooks}/codexcli/.codex/hooks.json "$out"
  '';
in
{
  environment.etc."codex/requirements.toml".source = codexManagedHooksRequirements;
}
