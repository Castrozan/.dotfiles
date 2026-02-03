# Zanoni's Home Manager Configuration
{ username, specialArgs, ... }:
let
  timestamp = builtins.toString builtins.currentTime;
in
{
  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    backupFileExtension = "bkp-${timestamp}";

    extraSpecialArgs = specialArgs // {
      inherit username;
    };
    users.${username} = import ./home.nix;
  };
}
