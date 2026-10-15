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
  programs.prismlauncher = {
    enable = true;
    package = latest.prismlauncher;
    settings = lib.optionalAttrs (isNixOS && hostname == "chise") {
      UseDiscreteGpu = true;
    };
  };

  home.activation.minecraftNvidiaOffload = lib.mkIf (isNixOS && hostname == "chise") (
    lib.hm.dag.entryAfter [ "prismlauncherConfigActivation" ] ''
      for instanceConfiguration in ${lib.escapeShellArg "${config.xdg.dataHome}/PrismLauncher/instances"}/*/instance.cfg; do
        [ -f "$instanceConfiguration" ] || continue
        run ${lib.getExe pkgs.crudini} --set --ini-options=nospace "$instanceConfiguration" General UseDiscreteGpu true
        instanceWrapperCommand="$(${lib.getExe pkgs.crudini} --get "$instanceConfiguration" General WrapperCommand 2>/dev/null || true)"
        case "$instanceWrapperCommand" in
          '"env -u __GLX_VENDOR_LIBRARY_NAME -u GBM_BACKEND -u __NV_PRIME_RENDER_OFFLOAD -u __NV_PRIME_RENDER_OFFLOAD_PROVIDER -u __VK_LAYER_NV_optimus DRI_PRIME=pci-0000_05_00_0"') run ${lib.getExe pkgs.crudini} --set --ini-options=nospace "$instanceConfiguration" General WrapperCommand "" ;;
        esac
      done
    ''
  );
}
