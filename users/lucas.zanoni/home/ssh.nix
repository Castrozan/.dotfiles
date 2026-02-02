{
  programs.ssh =
    let
      sshHostsPath = ../../../private-config/ssh-hosts.nix;
      sshHosts = if builtins.pathExists sshHostsPath then import sshHostsPath else { };
    in
    {
      enable = true;
      enableDefaultConfig = false;
      matchBlocks = {
        "*" = { };
      }
      // (
        if sshHosts ? dellg15 then
          {
            "dellg15" = {
              hostname = sshHosts.dellg15;
              user = "zanoni";
              identityFile = "~/.ssh/id_ed25519";
            };
          }
        else
          { }
      )
      // {
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
