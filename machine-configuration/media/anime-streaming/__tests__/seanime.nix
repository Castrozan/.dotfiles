{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  seanimeModule = import ../seanime-home-manager.nix {
    config.home.homeDirectory = "/home/zanoni";
    inherit lib pkgs;
  };
  seanimeUnit = seanimeModule.systemd.user.services.seanime;
  provisionerUnit = seanimeModule.systemd.user.services.seanime-provisioner;
  serverCommand = seanimeUnit.Service.ExecStart;
  serverEnvironment = lib.concatStringsSep " " seanimeUnit.Service.Environment;
  provisionerEnvironment = lib.concatStringsSep " " provisionerUnit.Service.Environment;
  providerManifest =
    builtins.fromJSON
      seanimeModule.home.file.".local/share/seanime/extensions/prowlarr-torrent-provider.json".text;
  providerPayload = builtins.readFile ../prowlarr-anime-torrent-provider.js;
  provisionerSource = builtins.readFile ../scripts/seanime_provisioner/__main__.py;
  provisionerConfigurationSource = builtins.readFile ../scripts/seanime_provisioner/seanime_configuration.py;
  moduleSource = builtins.readFile ../seanime-home-manager.nix;
in
{
  chise-seanime-is-tailnet-only =
    mkEvalCheck "chise-seanime-is-tailnet-only"
      (
        lib.hasInfix "--host=" serverCommand
        && !(lib.hasInfix "--host=0.0.0.0" serverCommand)
        && !(lib.hasInfix "0.0.0.0" moduleSource)
        && !(lib.hasInfix "funnel" (lib.toLower moduleSource))
      )
      "Seanime must bind only the private tailnet address and must never acquire a Funnel or wildcard listener";

  chise-seanime-uses-the-declared-web-port =
    mkEvalCheck "chise-seanime-uses-the-declared-web-port"
      (
        lib.hasInfix "--port=43211" serverCommand
        && lib.hasInfix "SEANIME_URL=http://" provisionerEnvironment
        && lib.hasInfix ":43211" provisionerEnvironment
      )
      "the server and provisioner must agree on port 43211 so the private stack tile reaches the service that is actually configured";

  chise-seanime-stream-cache-is-ephemeral =
    mkEvalCheck "chise-seanime-stream-cache-is-ephemeral"
      (
        seanimeUnit.Service.RuntimeDirectory == "seanime"
        && lib.hasInfix "TMPDIR=%t/seanime" serverEnvironment
        && lib.hasInfix ''"downloadDir": ""'' provisionerConfigurationSource
      )
      "torrent pieces must land under the per-session runtime directory rather than becoming a second persistent anime library";

  chise-seanime-peer-listener-keeps-the-dual-stack-default =
    mkEvalCheck "chise-seanime-peer-listener-keeps-the-dual-stack-default"
      (
        lib.hasInfix ''"torrentClientHost": ""'' provisionerConfigurationSource
        && lib.hasInfix ''"streamingServerHost": "127.0.0.1"'' provisionerConfigurationSource
      )
      "Seanime must choose compatible IPv4 and IPv6 peer listeners itself while keeping its HTTP streaming server on loopback";

  chise-seanime-does-not-import-streams =
    mkEvalCheck "chise-seanime-does-not-import-streams"
      (
        lib.hasInfix ''"addToLibrary": False'' provisionerConfigurationSource
        && lib.hasInfix ''"includeInLibrary": False'' provisionerConfigurationSource
        && lib.hasInfix ''"preloadNextStream": False'' provisionerConfigurationSource
      )
      "quick-watch streams must neither enter the tracked library nor preload the next episode behind the user's back";

  chise-seanime-prowlarr-provider-is-local =
    mkEvalCheck "chise-seanime-prowlarr-provider-is-local"
      (
        providerManifest.id == "prowlarr-torrent-provider"
        && providerManifest.manifestURI == ""
        && providerManifest.payloadURI == ""
        && providerManifest.payload == providerPayload
      )
      "the Prowlarr provider must ship from this repo instead of loading mutable extension code from a third-party branch at startup";

  chise-seanime-prowlarr-provider-does-not-eagerly-download =
    mkEvalCheck "chise-seanime-prowlarr-provider-does-not-eagerly-download"
      (
        !(lib.hasInfix "Promise.all" providerPayload)
        && lib.hasInfix ''url.searchParams.delete("apikey")'' providerPayload
        && lib.hasInfix ''redirect: "manual"'' providerPayload
        && lib.hasInfix "$torrentUtils.getMagnetLinkFromTorrentData" providerPayload
      )
      "searching must return metadata immediately, strip Prowlarr credentials from result URLs, and resolve torrent metadata only after one result is selected";

  chise-seanime-reads-prowlarr-key-at-runtime =
    mkEvalCheck "chise-seanime-reads-prowlarr-key-at-runtime"
      (
        lib.hasInfix "SEANIME_PROWLARR_CONFIG_FILE=/home/zanoni/arr-stack/config/prowlarr/config.xml" provisionerEnvironment
        && lib.hasInfix "read_prowlarr_api_key" provisionerSource
        && !(lib.hasInfix "prowlarrApiKey =" moduleSource)
      )
      "the Prowlarr API key must come from the live app config and never enter the public Nix source or store-built extension manifest";

  chise-seanime-launches-streams-with-mpv =
    mkEvalCheck "chise-seanime-launches-streams-with-mpv"
      (
        lib.hasInfix "mediaPlayer.defaultPlayer" provisionerSource
        && lib.hasInfix "mediaPlayer.mpvArgs" provisionerSource
        && lib.hasInfix "--no-terminal --vo=gpu-next --gpu-context=wayland" provisionerConfigurationSource
        && lib.hasInfix (builtins.unsafeDiscardStringContext "SEANIME_MPV_PATH=${pkgs.mpv}/bin/mpv") provisionerEnvironment
        && lib.hasInfix (builtins.unsafeDiscardStringContext "${pkgs.mpv}/bin") serverEnvironment
      )
      "the server must use a Nix-resolved mpv rather than depending on whatever PATH the user manager happened to inherit";

  chise-seanime-starts-and-reconciles-with-the-user-session =
    mkEvalCheck "chise-seanime-starts-and-reconciles-with-the-user-session"
      (
        seanimeUnit.Install.WantedBy == [ "default.target" ]
        && provisionerUnit.Install.WantedBy == [ "default.target" ]
        && provisionerUnit.Unit.Requires == [ "seanime.service" ]
        && provisionerUnit.Service.TimeoutStartSec == "90s"
      )
      "both services must run at login and the reconciler must stay within the user-generation activation timeout";

  chise-seanime-provider-changes-restart-the-provisioner =
    mkEvalCheck "chise-seanime-provider-changes-restart-the-provisioner"
      (provisionerUnit.Unit.X-Restart-Triggers == [ (builtins.hashString "sha256" providerPayload) ])
      "a provider payload change must rerun the provisioner so Seanime reloads the extension without a manual restart";
}
