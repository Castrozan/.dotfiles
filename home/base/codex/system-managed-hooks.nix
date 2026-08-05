{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  ...
}:
let
  codexHookEvents =
    import ../../../agent-harness/hooks/integrations/codex/codex-hooks-configuration.nix
      {
        inherit
          pkgs
          lib
          hostname
          isDarwin
          ;
      };
  codexRequirementsTomlFormat = pkgs.formats.toml { };
  codexManagedHooksRequirements =
    codexRequirementsTomlFormat.generate "codex-managed-requirements.toml"
      {
        features.hooks = true;
        hooks = codexHookEvents;
      };
in
{
  environment.etc."codex/requirements.toml".source = codexManagedHooksRequirements;
}
