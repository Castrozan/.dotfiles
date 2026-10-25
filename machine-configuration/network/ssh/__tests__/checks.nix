{
  self,
  helpers,
  lib,
  pkgs,
  ...
}:
let
  systemConfiguration = self.nixosConfigurations.chise.config;
  configuration = systemConfiguration.home-manager.users.zanoni;
  libvirtSource = "${systemConfiguration.virtualisation.libvirtd.package}/etc/ssh/ssh_config.d/30-libvirt-ssh-proxy.conf";
  systemdSource = "${systemConfiguration.systemd.package}/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf";
  activation = configuration.home.activation.materializeUserOwnedSshConfig;
in
{
  domain-ssh-config-preserves-sandbox-ownership-checks =
    helpers.mkEvalCheck "domain-ssh-config-preserves-sandbox-ownership-checks"
      (
        configuration.home.file.".ssh/config".target == ".ssh/config.nix-source"
        && lib.elem "linkGeneration" activation.after
        && lib.hasInfix "materialize_ssh_config.py" activation.data
        && lib.hasInfix "${configuration.home.homeDirectory}/.ssh/config" activation.data
      )
      "Home Manager must activate a user-owned SSH config from its current generated source without changing sandbox or SSH checks";

  domain-ssh-system-includes-have-caller-owned-copies =
    helpers.mkEvalCheck "domain-ssh-system-includes-have-caller-owned-copies"
      (builtins.all (
        username:
        builtins.all
          (
            snippet:
            let
              entry = systemConfiguration.environment.etc."ssh/caller-configs/${username}/${snippet.name}";
            in
            entry.user == username && entry.mode == "0444" && toString entry.source == snippet.source
          )
          [
            {
              name = "30-libvirt-ssh-proxy.conf";
              source = libvirtSource;
            }
            {
              name = "20-systemd-ssh-proxy.conf";
              source = systemdSource;
            }
          ]
      ) (builtins.attrNames systemConfiguration.users.users))
      "Every configured local caller, including root, must retain the original proxy snippets under its own trusted ownership";

  domain-ssh-system-config-preserves-all-options =
    pkgs.runCommand "check-ssh-system-config-preserves-all-options"
      { nativeBuildInputs = [ pkgs.python312 ]; }
      ''
        python - ${
          pkgs.writeText "original-system-ssh-config"
            systemConfiguration.environment.etc."ssh/ssh_config".text
        } ${
          systemConfiguration.environment.etc."ssh/ssh_config".source
        } ${libvirtSource} ${systemdSource} <<'PYTHON'
        from pathlib import Path
        import sys
        original, effective, libvirt, systemd = sys.argv[1:]
        expected = Path(original).read_text().replace(libvirt, "/etc/ssh/caller-configs/%u/30-libvirt-ssh-proxy.conf").replace(systemd, "/etc/ssh/caller-configs/%u/20-systemd-ssh-proxy.conf")
        assert Path(effective).read_text() == expected
        assert "Include /etc/ssh/caller-configs/%u/30-libvirt-ssh-proxy.conf" in expected
        assert "Include /etc/ssh/caller-configs/%u/20-systemd-ssh-proxy.conf" in expected
        PYTHON
        touch "$out"
      '';
}
