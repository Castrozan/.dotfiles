{
  description = "Public stand-in for the private orchestrator input";

  outputs = _: {
    homeManagerModules.default =
      { lib, ... }:
      {
        options.programs.orchestrator.userModelPath = lib.mkOption {
          type = lib.types.nullOr lib.types.str;
          default = null;
        };
      };
  };
}
