{ pkgs, healthCheckLib, ... }:
{
  home.packages = [
    (pkgs.stdenv.mkDerivation {
      name = "workspace-switcher-send";
      src = ./workspace-switcher-send.c;
      unpackPhase = "true";
      buildPhase = "$CC -O2 -o workspace-switcher-send $src";
      installPhase = "mkdir -p $out/bin && cp workspace-switcher-send $out/bin/";
    })
  ];

  healthCheck.probes = [
    (healthCheckLib.mkLaunchdProbe {
      name = "darwin app switcher daemon";
      label = "com.dotfiles.workspace-window-switcher";
    })
  ];
}
