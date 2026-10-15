{
  latest,
  pkgs,
  lib,
  config,
  isNixOS,
  hostname,
  ...
}:
{
  home.packages = [ latest.prismlauncher ];

  home.activation.minecraftNvidiaOffload = lib.mkIf (isNixOS && hostname == "chise") (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${pkgs.bash}/bin/bash ${./scripts/configure_minecraft_gpu.sh} \
        ${lib.escapeShellArg "${config.xdg.dataHome}/PrismLauncher"} ${lib.getExe pkgs.crudini}
    ''
  );
}
