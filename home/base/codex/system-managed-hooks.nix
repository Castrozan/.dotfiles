{
  pkgs,
  lib,
  hostname,
  ...
}:
let
  codexHookEvents = import ./hooks/configuration.nix { inherit pkgs lib hostname; };
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
