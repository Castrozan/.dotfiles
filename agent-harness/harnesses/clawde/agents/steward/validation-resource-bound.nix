{ lib, pkgs, ... }:
let
  boundedSliceName = "background-steward";
  boundedScopeNamePrefixes = [
    "steward-validate"
    "steward-activation"
  ];
in
{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
    systemd.user.slices.${boundedSliceName} = {
      Unit.Description = "Steward revision validations held below the interactive desktop";
      Slice.MemoryHigh = "3G";
    };

    xdg.configFile = lib.listToAttrs (
      map (
        prefix:
        lib.nameValuePair "systemd/user/${prefix}-.scope.d/${boundedSliceName}.conf" {
          text = ''
            [Scope]
            Slice=${boundedSliceName}.slice
          '';
        }
      ) boundedScopeNamePrefixes
    );
  };
}
