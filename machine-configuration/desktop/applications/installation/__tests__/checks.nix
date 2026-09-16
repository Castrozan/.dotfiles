{ helpers, lib, ... }:
let
  darwinConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    ../darwin-application-links-home-manager.nix
  ];
  linuxConfiguration = helpers.homeManagerTestConfiguration [
    ../darwin-application-links-home-manager.nix
  ];
in
{
  domain-desktop-darwin-applications-link-without-app-management =
    helpers.mkEvalCheck "domain-desktop-darwin-applications-link-without-app-management"
      (
        darwinConfiguration.targets.darwin.linkApps.enable
        && !darwinConfiguration.targets.darwin.copyApps.enable
        && darwinConfiguration.targets.darwin.linkApps.directory == "Applications/Home Manager Apps"
        && lib.hasSuffix "-home-manager-applications/Applications" (
          toString darwinConfiguration.home.file."Applications/Home Manager Apps".source
        )
        && !(darwinConfiguration.home.activation ? checkAppManagementPermission)
        && !(darwinConfiguration.home.activation ? copyApps)
      )
      "Darwin rebuilds must link the managed application directory instead of modifying app bundles or resetting App Management permissions";

  domain-desktop-darwin-application-links-leave-linux-unchanged =
    helpers.mkEvalCheck "domain-desktop-darwin-application-links-leave-linux-unchanged"
      (
        !linuxConfiguration.targets.darwin.linkApps.enable
        && !linuxConfiguration.targets.darwin.copyApps.enable
        && !(linuxConfiguration.home.file ? "Applications/Home Manager Apps")
      )
      "Darwin application linking must not create macOS application paths on Linux";
}
