{
  self,
  helpers,
  lib,
  ...
}:
let
  configuration = self.nixosConfigurations.chise.config.home-manager.users.zanoni;
  activation = configuration.home.activation.materializeUserOwnedSshConfig;
in
{
  domain-ssh-config-preserves-sandbox-ownership-checks =
    helpers.mkEvalCheck "domain-ssh-config-preserves-sandbox-ownership-checks"
      (
        configuration.home.file.".ssh/config".target == ".ssh/config.nix-source"
        && lib.elem "linkGeneration" activation.after
        && lib.hasInfix "materialize_ssh_config.py" activation.data
        && lib.hasInfix "${configuration.home.homeDirectory}/.ssh/config" activation.data
      )
      "Home Manager must activate a user-owned SSH config from its current generated source without changing sandbox or SSH checks";
}
