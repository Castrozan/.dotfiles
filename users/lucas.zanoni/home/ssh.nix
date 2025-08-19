{
  programs.ssh = {
    enable = true;
    matchBlocks = {
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
