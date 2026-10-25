{ lib, pkgs, ... }:
let
  validationSliceName = "background-steward";
  validationScopeNamePrefix = "steward-validate";
in
{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
    systemd.user.slices.${validationSliceName} = {
      Unit.Description = "Steward revision validations held below the interactive desktop";
      Slice.MemoryHigh = "3G";
    };

    xdg.configFile."systemd/user/${validationScopeNamePrefix}-.scope.d/${validationSliceName}.conf".text =
      ''
        [Scope]
        Slice=${validationSliceName}.slice
      '';
  };
}
