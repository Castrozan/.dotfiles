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
      hostname = "anime.lucaszanoni.com";
      proxyPort = 9447;
      upstreamUrl = "http://${chiseTailnetBindAddress}:4568";
      loginLocationRegexes = [ ];
    }
    {
      hostname = "suwayomi.lucaszanoni.com";
      proxyPort = 9452;
      upstreamUrl = "http://${chiseTailnetBindAddress}:4567";
      loginLocationRegexes = [ ];
    }
    {
      hostname = "readmeabook.lucaszanoni.com";
      proxyPort = 9454;
      upstreamUrl = "http://${chiseTailnetBindAddress}:3030";
      loginLocationRegexes = [ "^/api/auth/(local/login|admin/login|token/login|register)$" ];
    }
    {
      hostname = "audiobookshelf.lucaszanoni.com";
      proxyPort = 9455;
      upstreamUrl = "http://${chiseTailnetBindAddress}:13378";
      loginLocationRegexes = [ "^/login$" ];
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
