{ homeDir }:
rec {
  runtimeRootRelativeToHome = "clawde";
  runtimeRootDirectory = "${homeDir}/${runtimeRootRelativeToHome}";

  hostIdentityRelativeToHome = "${runtimeRootRelativeToHome}/host-identity.json";
  hostIdentityFile = "${homeDir}/${hostIdentityRelativeToHome}";

  fleetManifestRelativeToHome = "${runtimeRootRelativeToHome}/fleet.json";
  fleetManifestFile = "${homeDir}/${fleetManifestRelativeToHome}";
}
