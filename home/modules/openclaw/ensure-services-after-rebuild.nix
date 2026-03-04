{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;
  gatewayServiceEnabled = openclaw.gatewayService.enable;
  watcherServiceEnabled = openclaw.restartWatcher.enable;

  servicesToEnsure =
    lib.optional gatewayServiceEnabled "openclaw-gateway.service"
    ++ lib.optional watcherServiceEnabled "openclaw-restart-watcher.service";
in
{
  config = lib.mkIf (servicesToEnsure != [ ]) {
    home.activation.ensureOpenclawServicesAfterReload = lib.hm.dag.entryAfter [ "reloadSystemd" ] ''
      run systemctl --user start ${lib.escapeShellArgs servicesToEnsure} 2>/dev/null || true
    '';
  };
}
