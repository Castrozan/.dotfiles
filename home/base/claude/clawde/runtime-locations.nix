{ homeDir }:
rec {
  runtimeRootRelativeToHome = "clawde";
  runtimeRootDirectory = "${homeDir}/${runtimeRootRelativeToHome}";

  hostIdentityRelativeToHome = "${runtimeRootRelativeToHome}/host-identity.json";
  hostIdentityFile = "${homeDir}/${hostIdentityRelativeToHome}";

  fleetManifestRelativeToHome = "${runtimeRootRelativeToHome}/fleet.json";
  fleetManifestFile = "${homeDir}/${fleetManifestRelativeToHome}";

  agentInstructionsRelativeToHome = name: "${runtimeRootRelativeToHome}/instructions/${name}.md";
  agentInstructionsFile = name: "${homeDir}/${agentInstructionsRelativeToHome name}";

  agentLaunchConfigRelativeToHome = name: "${runtimeRootRelativeToHome}/launch-config/${name}.json";
  agentLaunchConfigFile = name: "${homeDir}/${agentLaunchConfigRelativeToHome name}";
}
