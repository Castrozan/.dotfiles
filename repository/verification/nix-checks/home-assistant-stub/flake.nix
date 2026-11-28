{
  description = "Public stand-in for the private Home Assistant input so CI can evaluate the public flake";

  outputs =
    _:
    let
      homeAssistantModule =
        { lib, ... }:
        let
          unconstrainedSettings = lib.mkOption {
            type = lib.types.lazyAttrsOf lib.types.anything;
            default = { };
          };
        in
        {
          options.homeAssistant = unconstrainedSettings;
        };
    in
    {
      nixosModules.default = homeAssistantModule;
      homeManagerModules = {
        default = homeAssistantModule;
        remote = homeAssistantModule;
      };
    };
}
