{
  description = "Public stand-in for the private arr-stack input so CI never fetches it";

  outputs = _: {
    nixosModules.default =
      { lib, ... }:
      let
        unconstrainedSettings = lib.mkOption {
          type = lib.types.lazyAttrsOf lib.types.anything;
          default = { };
        };
      in
      {
        options = {
          services.arrStack = unconstrainedSettings;
          custom.arrMediaLoginRateLimitProxy = unconstrainedSettings;
        };
      };
  };
}
