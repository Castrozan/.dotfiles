{
  description = "Public CI stand-in for the private commit-provenance flake";

  outputs = _: {
    homeManagerModules.default =
      { lib, ... }:
      {
        options.programs.commit-provenance = {
          machineName = lib.mkOption {
            type = lib.types.str;
            default = "";
          };
          sessionControlPythonPath = lib.mkOption {
            type = lib.types.path;
          };
        };
      };
  };
}
