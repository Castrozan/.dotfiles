{
  helpers,
  lib,
  pkgs,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  homeDirectory = "/home/zanoni";
  tailnetBindAddress = import ../../tailnet-bind-address.nix { inherit lib; };
  suwayomiModule = import ../suwayomi-server-nixos.nix {
    config.users.users.zanoni.home = homeDirectory;
    inherit lib pkgs;
  };
  suwayomiUnit = suwayomiModule.systemd.services.suwayomi-server;
  command = suwayomiUnit.serviceConfig.ExecStart;
  chiseConfiguration = self.nixosConfigurations.chise.config;
  downloadsVolume = "--volume ${homeDirectory}/arr-stack/data/manga:/home/suwayomi/.local/share/Tachidesk/downloads";
  dataVolume = "--volume ${homeDirectory}/.local/share/Tachidesk:/home/suwayomi/.local/share/Tachidesk";
in
{
  chise-suwayomi-runs-in-the-official-pinned-container =
    mkEvalCheck "chise-suwayomi-runs-in-the-official-pinned-container"
      (
        lib.hasInfix "ghcr.io/suwayomi/suwayomi-server:v2.3.2243-preview@sha256:2b95476844614748285ecba0deef97cb8eabd17c6ccb58d136f829ec20b8040f" command
        && lib.hasInfix "--user 1000:100" command
        && suwayomiUnit.wantedBy == [ "multi-user.target" ]
        && !(chiseConfiguration.home-manager.users.zanoni.systemd.user.services ? suwayomi-server)
      )
      "Suwayomi must use the official non-root KCEF image pinned to the same server release and digest, with the escaped desktop JVM service retired so every process stays inside the container cgroup";

  chise-suwayomi-is-tailnet-only-and-drive-guarded =
    mkEvalCheck "chise-suwayomi-is-tailnet-only-and-drive-guarded"
      (
        lib.hasInfix "--publish ${tailnetBindAddress}:4567:4567" command
        && !(lib.hasInfix "--publish 0.0.0.0" command)
        && suwayomiUnit.unitConfig.RequiresMountsFor == [ "${homeDirectory}/arr-stack/data" ]
        && builtins.elem "tailscaled.service" suwayomiUnit.after
        && builtins.elem "home-manager-zanoni.service" suwayomiUnit.after
      )
      "the loginless server must publish only on chise's tailnet address, wait for Tailscale and Home Manager, and refuse startup when the media drive is absent";

  chise-suwayomi-preserves-state-and-kavita-downloads =
    mkEvalCheck "chise-suwayomi-preserves-state-and-kavita-downloads"
      (
        lib.hasInfix "${downloadsVolume} ${dataVolume}" command
        && lib.hasInfix "--env DOWNLOAD_AS_CBZ=true" command
      )
      "the container migration must mount the existing downloads before the whole Tachidesk state tree, preserving the database and placing CBZ chapters in Kavita's existing manga root as required by the official image";

  chise-suwayomi-keeps-webview-and-bundled-interface =
    mkEvalCheck "chise-suwayomi-keeps-webview-and-bundled-interface"
      (
        lib.hasInfix "--env KCEF_ENABLED=true" command
        && lib.hasInfix "--env WEB_UI_CHANNEL=bundled" command
        && lib.hasInfix "--env WEB_UI_UPDATE_INTERVAL=0" command
      )
      "the official container must retain KCEF for browser-backed extensions while serving only its pinned bundled interface without mutable update checks";

  chise-suwayomi-has-layered-memory-and-health-bounds =
    mkEvalCheck "chise-suwayomi-has-layered-memory-and-health-bounds"
      (
        lib.hasInfix "--cgroup-parent media-containers.slice" command
        && lib.hasInfix "--memory 3g" command
        && lib.hasInfix ''--env "JAVA_TOOL_OPTIONS=-Xms128m -Xmx768m"'' command
        && lib.hasInfix ''--health-cmd "curl -fsS http://127.0.0.1:4567/api/v1/health"'' command
        && lib.hasInfix "--health-start-period 120s" command
      )
      "Suwayomi must keep its JVM heap modest, admit measured native Chromium overhead within a 3 GiB container ceiling, join the aggregate media slice, and report application health through its supported endpoint";

  chise-suwayomi-restarts-without-rate-limiting =
    mkEvalCheck "chise-suwayomi-restarts-without-rate-limiting"
      (
        suwayomiUnit.serviceConfig.Restart == "always" && suwayomiUnit.unitConfig.StartLimitIntervalSec == 0
      )
      "Suwayomi must restart after every exit without exhausting systemd's start limiter while its tailnet publish is settling";
}
