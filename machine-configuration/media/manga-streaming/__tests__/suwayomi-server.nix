{
  helpers,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  composeText = builtins.readFile ../../arr-stack/stack/docker-compose.yml;
  serviceBodyParts = lib.splitString "\n  suwayomi:\n" composeText;
  suwayomiServiceBody =
    if builtins.length serviceBodyParts == 2 then
      lib.head (lib.splitString "\n  miwayomi:\n" (lib.elemAt serviceBodyParts 1))
    else
      "";
  chiseConfiguration = self.nixosConfigurations.chise.config;
  driveGuardFrontEndServices =
    chiseConfiguration.custom.arrStackOnDemandSupervisor.mountGuard.frontEndServices;
  extensionRepositoryUnit = chiseConfiguration.systemd.services.suwayomi-extension-repositories;
  dockerBridgeAllowedTcpPorts =
    lib.attrByPath
      [
        "networking"
        "firewall"
        "interfaces"
        "docker0"
        "allowedTCPPorts"
      ]
      [ ]
      chiseConfiguration;
in
{
  chise-suwayomi-runs-as-an-arr-stack-front-end =
    mkEvalCheck "chise-suwayomi-runs-as-an-arr-stack-front-end"
      (
        lib.hasInfix "image: ghcr.io/suwayomi/suwayomi-server:v2.3.2243-preview@sha256:2b95476844614748285ecba0deef97cb8eabd17c6ccb58d136f829ec20b8040f" suwayomiServiceBody
        && lib.hasInfix "container_name: arr-suwayomi" suwayomiServiceBody
        && lib.hasInfix "restart: unless-stopped" suwayomiServiceBody
        && lib.hasInfix "user: \"\${PUID}:\${PGID}\"" suwayomiServiceBody
        && lib.hasInfix "- arrnet" suwayomiServiceBody
        && builtins.elem "suwayomi" driveGuardFrontEndServices
        && !(chiseConfiguration.systemd.services ? suwayomi-server)
      )
      "Suwayomi must be an ordinary always-on arr-stack Compose front end, restored by the same drive guard as Jellyfin, Kavita, and Miwayomi, with no parallel standalone container unit";

  chise-suwayomi-is-tailnet-only-and-drive-guarded =
    mkEvalCheck "chise-suwayomi-is-tailnet-only-and-drive-guarded"
      (
        lib.hasInfix "\"\${ARR_BIND_ADDR:?set in ~/arr-stack/.env}:4567:4567\"" suwayomiServiceBody
        && !(lib.hasInfix ''- "0.0.0.0:4567:4567"'' suwayomiServiceBody)
        && builtins.elem "arr-stack-front-ends-compose.service" extensionRepositoryUnit.after
        && builtins.elem "arr-stack-front-ends-compose.service" extensionRepositoryUnit.requires
      )
      "the loginless server must publish only on chise's tailnet address, and its repository reconciler must wait for the Compose applicator that restores the front ends";

  chise-suwayomi-preserves-state-and-kavita-downloads =
    mkEvalCheck "chise-suwayomi-preserves-state-and-kavita-downloads"
      (
        lib.hasInfix "\${ARR_CONFIG_ROOT}/suwayomi:/home/suwayomi/.local/share/Tachidesk" suwayomiServiceBody
        && lib.hasInfix "\${ARR_DATA_ROOT}/manga:/home/suwayomi/.local/share/Tachidesk/downloads" suwayomiServiceBody
        && lib.hasInfix "DOWNLOAD_AS_CBZ: \"true\"" suwayomiServiceBody
      )
      "Suwayomi must keep its state under the arr-stack config root and write CBZ downloads into the shared manga tree Kavita reads";

  chise-suwayomi-keeps-webview-and-bundled-interface =
    mkEvalCheck "chise-suwayomi-keeps-webview-and-bundled-interface"
      (
        lib.hasInfix "KCEF_ENABLED: \"true\"" suwayomiServiceBody
        && lib.hasInfix "WEB_UI_CHANNEL: bundled" suwayomiServiceBody
        && lib.hasInfix "WEB_UI_UPDATE_INTERVAL: \"0\"" suwayomiServiceBody
      )
      "the Compose service must retain KCEF for browser-backed extensions while serving only its pinned bundled interface without mutable update checks";

  chise-suwayomi-has-layered-memory-and-health-bounds =
    mkEvalCheck "chise-suwayomi-has-layered-memory-and-health-bounds"
      (
        lib.hasInfix "<<: *media-3g" suwayomiServiceBody
        && lib.hasInfix "JAVA_TOOL_OPTIONS: -Xms128m -Xmx768m" suwayomiServiceBody
        && lib.hasInfix ''test: ["CMD", "curl", "-fsS", "http://127.0.0.1:4567/api/v1/health"]'' suwayomiServiceBody
        && lib.hasInfix "start_period: 120s" suwayomiServiceBody
      )
      "Suwayomi must keep its JVM heap modest, admit native Chromium overhead within a 3 GiB container ceiling, join the shared media slice, and expose application health";

  chise-suwayomi-uses-the-stack-solver =
    mkEvalCheck "chise-suwayomi-uses-the-stack-solver"
      (
        lib.hasInfix "FLARESOLVERR_ENABLED: \"true\"" suwayomiServiceBody
        && lib.hasInfix "FLARESOLVERR_URL: http://flaresolverr:8191" suwayomiServiceBody
        && lib.hasInfix "flaresolverr:\n        condition: service_healthy" suwayomiServiceBody
        && !(builtins.elem 8191 dockerBridgeAllowedTcpPorts)
      )
      "Suwayomi must reach FlareSolverr over the shared Compose network and wait for its health check instead of leaving that network to re-enter through a host firewall exception";
}
