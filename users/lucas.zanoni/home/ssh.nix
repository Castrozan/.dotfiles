{
  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    matchBlocks = {
      "*" = { };
      "dellg15" = {
        hostname = "100.94.11.81";
        user = "zanoni";
        identityFile = "~/.ssh/id_ed25519";
      };
      "gitlab.com" = {
        hostname = "gitlab.services.betha.cloud";
        user = "git";
        identityFile = "~/.ssh/id_ed25519";
      };
      "gitlab.services.betha.cloud" = {
        hostname = "gitlab.services.betha.cloud";
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
