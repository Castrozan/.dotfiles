{
  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    matchBlocks = {
      "*" = { };
      "dellg15" = {
        hostname = "192.168.7.29";
        port = 22;
        user = "zanoni";
        identityFile = "~/.ssh/id_ed25519";
      };
      "dellg15-remote" = {
        hostname = "REDACTED_IP_1";
        port = 22;
        user = "zanoni";
        identityFile = "~/.ssh/id_ed25519";
      };
      "gitlab.com" = {
        hostname = "gitlab.service.betha.cloud";
        user = "git";
        identityFile = "~/.ssh/id_ed25519";
      };
      "github.com" = {
        hostname = "github.com";
        user = "git";
        identityFile = "~/.ssh/id_rsa";
      };
    };
  };
}
