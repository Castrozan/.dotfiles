{ config, ... }:
{
  boot = {
    kernelModules = [ "tcp_bbr" ];

    kernel.sysctl = {
      "net.core.default_qdisc" = "fq";
      "net.ipv4.tcp_congestion_control" = "bbr";

      "net.core.rmem_max" = 16777216;
      "net.core.wmem_max" = 16777216;
      "net.core.rmem_default" = 1048576;
      "net.core.wmem_default" = 1048576;
      "net.ipv4.tcp_rmem" = "4096 1048576 16777216";
      "net.ipv4.tcp_wmem" = "4096 1048576 16777216";

      "net.ipv4.tcp_fastopen" = 3;
      "net.ipv4.tcp_slow_start_after_idle" = 0;
      "net.ipv4.tcp_mtu_probing" = 1;

      "net.core.netdev_max_backlog" = 16384;
    };
  };

  networking.networkmanager = {
    wifi.powersave = false;
    ensureProfiles = {
      environmentFiles = [ config.age.secrets.wifi-psk-zanoni.path ];
      profiles.zanoni-5ghz = {
        connection = {
          id = "Zanoni";
          type = "wifi";
        };
        wifi = {
          ssid = "Zanoni";
          band = "a";
          mode = "infrastructure";
        };
        wifi-security = {
          key-mgmt = "wpa-psk";
          psk = "$WIFI_PSK_ZANONI";
        };
      };
    };
  };
}
