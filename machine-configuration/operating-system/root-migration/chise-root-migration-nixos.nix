{
  config,
  lib,
  pkgs,
  ...
}:
let
  sourceFilesystemUuid = "75857f97-64bd-4060-bc8b-60b3224fef48";
  destinationFilesystemUuid = "328f423f-3f0b-4a00-a4a9-71a0f6b645ca";
in
{
  assertions = [
    {
      assertion = !config.boot.initrd.systemd.enable;
      message = "The temporary chise root migration requires the shell initrd.";
    }
    {
      assertion = config.fileSystems."/".device == "/dev/disk/by-uuid/${destinationFilesystemUuid}";
      message = "The temporary chise root migration must boot its prepared destination filesystem.";
    }
  ];

  boot.initrd.extraUtilsCommands = ''
    copy_bin_and_libs ${pkgs.rsync}/bin/rsync
    copy_bin_and_libs ${pkgs.util-linux}/bin/findmnt
    cp ${./scripts/finalize-root-migration.sh} $out/bin/finalize-root-migration
    chmod +x $out/bin/finalize-root-migration
    mkdir -p $out/etc/root-migration
    cp ${./scripts/root-copy-excludes} $out/etc/root-migration/excludes
  '';

  boot.initrd.extraUtilsCommandsTest = ''
    $out/bin/rsync --version
    $out/bin/findmnt --version
    $out/bin/ash -n $out/bin/finalize-root-migration
  '';

  boot.initrd.postMountCommands = lib.mkAfter ''
    while ! "$extraUtils/bin/ash" "$extraUtils/bin/finalize-root-migration" \
      ${lib.escapeShellArg sourceFilesystemUuid} ${lib.escapeShellArg destinationFilesystemUuid} \
      /mnt-root "$extraUtils/etc/root-migration/excludes"; do
      echo "Root synchronization failed. Reboot and select the previous NixOS generation to use the original root."
      fail
    done
  '';
}
