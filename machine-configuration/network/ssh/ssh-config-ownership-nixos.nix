{
  config,
  lib,
  pkgs,
  ...
}:
let
  proxySnippets =
    lib.optional (config.virtualisation.libvirtd.enable && config.virtualisation.libvirtd.sshProxy) {
      name = "30-libvirt-ssh-proxy.conf";
      source = "${config.virtualisation.libvirtd.package}/etc/ssh/ssh_config.d/30-libvirt-ssh-proxy.conf";
    }
    ++ lib.optional config.programs.ssh.systemd-ssh-proxy.enable {
      name = "20-systemd-ssh-proxy.conf";
      source = "${config.systemd.package}/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf";
    };
  snippetTarget = username: snippet: "ssh/caller-configs/${username}/${snippet.name}";
  callerFiles = lib.concatMap (
    username:
    map (
      snippet:
      lib.nameValuePair (snippetTarget username snippet) {
        inherit (snippet) source;
        mode = "0444";
        user = username;
      }
    ) proxySnippets
  ) (builtins.attrNames config.users.users);
  sourceConfiguration = config.environment.etc."ssh/ssh_config".text;
  callerConfiguration = lib.replaceStrings (map (snippet: snippet.source) proxySnippets) (map (
    snippet: "/etc/${snippetTarget "%u" snippet}"
  ) proxySnippets) sourceConfiguration;
in
{
  environment.etc = lib.listToAttrs callerFiles // {
    "ssh/ssh_config".source = lib.mkForce (pkgs.writeText "ssh-caller-config" callerConfiguration);
  };
}
