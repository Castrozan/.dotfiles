{ lib, ... }:
let
  tailnetBindAddress = import ../tailnet-bind-address.nix { inherit lib; };
  streamingProxyExtraConfig = ''
    proxy_buffering off;
    proxy_request_buffering off;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
    proxy_set_header X-Forwarded-Proto https;
  '';
in
{
  services.nginx = {
    enable = true;
    recommendedOptimisation = true;
    recommendedProxySettings = true;
    appendHttpConfig = lib.mkAfter ''
      map $args $stremioInternalHlsArguments {
        default $args;
        "~*^mediaURL=https%3a%2f%2fstream[.]lucaszanoni[.]com%2fserver%2f%2f(?<stremioMediaPathAfterDoubleSlash>[^&]*)(?<stremioRemainingArguments>&.*)?$" "mediaURL=http%3A%2F%2F127.0.0.1%3A11470%2F$stremioMediaPathAfterDoubleSlash$stremioRemainingArguments";
        "~*^mediaURL=https%3a%2f%2fstream[.]lucaszanoni[.]com%2fserver%2f(?<stremioMediaPathAfterSingleSlash>[^&]*)(?<stremioRemainingSingleSlashArguments>&.*)?$" "mediaURL=http%3A%2F%2F127.0.0.1%3A11470%2F$stremioMediaPathAfterSingleSlash$stremioRemainingSingleSlashArguments";
      }
    '';
    virtualHosts.stremio-public-origin = {
      listen = [
        {
          addr = "127.0.0.1";
          port = 9446;
          ssl = false;
        }
      ];
      locations = {
        "/" = {
          proxyPass = "http://${tailnetBindAddress}:43212";
          proxyWebsockets = true;
          extraConfig = streamingProxyExtraConfig;
        };
        "/server/" = {
          proxyPass = "http://${tailnetBindAddress}:11470/";
          proxyWebsockets = true;
          extraConfig = streamingProxyExtraConfig;
        };
        "/hlsv2/" = {
          proxyPass = "http://${tailnetBindAddress}:11470";
          extraConfig = ''
            set $args $stremioInternalHlsArguments;
            proxy_buffering off;
            proxy_request_buffering off;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
          '';
        };
      };
    };
  };
}
