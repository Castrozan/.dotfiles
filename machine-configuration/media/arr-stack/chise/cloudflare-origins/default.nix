{ lib, ... }:
let
  chiseTailnetBindAddress = import ../../../tailnet-bind-address.nix { inherit lib; };
  arrStackCloudflareProxyApplications = [
    {
      hostname = "watch.lucaszanoni.com";
      proxyPort = 9443;
      upstreamUrl = "http://127.0.0.1:8096";
      loginLocationRegexes = [ "^/Users/AuthenticateByName" ];
    }
    {
      hostname = "request.lucaszanoni.com";
      proxyPort = 9444;
      upstreamUrl = "http://127.0.0.1:5055";
      loginLocationRegexes = [ "^/api/v1/auth/(jellyfin|plex|local)" ];
    }
    {
      hostname = "read.lucaszanoni.com";
      proxyPort = 9445;
      upstreamUrl = "http://127.0.0.1:5000";
      loginLocationRegexes = [
        "^/api/Account/(login|register|forgot-password|reset-password|confirm-password-reset)"
      ];
    }
    {
      hostname = "seanime.lucaszanoni.com";
      proxyPort = 9447;
      upstreamUrl = "http://${chiseTailnetBindAddress}:43211";
      loginLocationRegexes = [ ];
    }
    {
      hostname = "radarr.lucaszanoni.com";
      proxyPort = 9448;
      upstreamUrl = "http://${chiseTailnetBindAddress}:7878";
      loginLocationRegexes = [ "^/login$" ];
    }
    {
      hostname = "sonarr.lucaszanoni.com";
      proxyPort = 9449;
      upstreamUrl = "http://${chiseTailnetBindAddress}:8989";
      loginLocationRegexes = [ "^/login$" ];
    }
    {
      hostname = "prowlarr.lucaszanoni.com";
      proxyPort = 9450;
      upstreamUrl = "http://${chiseTailnetBindAddress}:9696";
      loginLocationRegexes = [ "^/login$" ];
    }
    {
      hostname = "bazarr.lucaszanoni.com";
      proxyPort = 9451;
      upstreamUrl = "http://${chiseTailnetBindAddress}:6767";
      loginLocationRegexes = [ "^/login$" ];
    }
    {
      hostname = "suwayomi.lucaszanoni.com";
      proxyPort = 9452;
      upstreamUrl = "http://${chiseTailnetBindAddress}:4567";
      loginLocationRegexes = [ ];
    }
    {
      hostname = "qbittorrent.lucaszanoni.com";
      proxyPort = 9453;
      upstreamUrl = "http://${chiseTailnetBindAddress}:8080";
      loginLocationRegexes = [ "^/api/v2/auth/login$" ];
    }
  ];
in
{
  custom = {
    cloudflareTunnelConnector.ingress = lib.mkAfter (
      map (application: {
        inherit (application) hostname;
        localServiceUrl = "http://127.0.0.1:${toString application.proxyPort}";
      }) arrStackCloudflareProxyApplications
      ++ [
        {
          hostname = "stream.lucaszanoni.com";
          localServiceUrl = "http://127.0.0.1:9446";
        }
      ]
    );

    arrMediaLoginRateLimitProxy = {
      enable = true;
      origins = map (application: {
        listenPort = application.proxyPort;
        inherit (application) upstreamUrl loginLocationRegexes;
      }) arrStackCloudflareProxyApplications;
    };
  };
}
