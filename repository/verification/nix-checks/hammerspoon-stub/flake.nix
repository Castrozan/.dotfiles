{
  description = "Evaluation-only substitute for the private Hammerspoon input in public CI";

  outputs = _: {
    isCiStub = true;

    homeManagerModules.default = { lib, ... }: {
      options.programs.hammerspoon = lib.mkOption {
        type = lib.types.attrsOf lib.types.anything;
        default = { };
      };
    };
  };
}
