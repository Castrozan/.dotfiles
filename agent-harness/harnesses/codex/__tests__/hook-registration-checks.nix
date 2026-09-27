{
  pkgs,
  lib,
  mkEvalCheck,
  cfg,
}:
let
  managed = import ../system-managed-hooks.nix {
    inherit pkgs lib;
    hostname = "test";
  };
  darwinFactory = builtins.readFile ../../../../repository/flake-assembly/darwin-machine-factory.nix;
  nixosFactory = builtins.readFile ../../../../repository/flake-assembly/nixos-machine-factory.nix;
in
{
  codex-hooks-config-managed-file = mkEvalCheck "codex-hooks-config-managed-file" (
    !(builtins.hasAttr ".codex/hooks.json" cfg.home.file)
    && builtins.hasAttr "codex/requirements.toml" managed.environment.etc
    && lib.hasInfix "../../agent-harness/harnesses/codex/system-managed-hooks.nix" darwinFactory
    && lib.hasInfix "../../agent-harness/harnesses/codex/system-managed-hooks.nix" nixosFactory
  ) "Rulesync-generated Codex hooks must retain managed trust on Darwin and NixOS";

  codex-hooks-generated-native-registrations =
    pkgs.runCommand "codex-hooks-generated-native-registrations" { }
      ''
        ${pkgs.python312}/bin/python3 ${../../../agent-instructions/rulesync/hooks/__tests__/verify_registrations.py} \
          ${managed.environment.etc."codex/requirements.toml".source} codex
        touch "$out"
      '';
}
