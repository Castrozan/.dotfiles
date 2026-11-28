{
  description = "Public CI interface for the private read-it-later input";
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";

  outputs = _: {
    skill = ./skill;
    homeManagerModules = {
      default =
        { lib, ... }:
        {
          options.programs.ril = lib.mkOption {
            type = lib.types.attrsOf lib.types.anything;
          };
        };
      watcher =
        { config, ... }:
        {
          clawde.agents.ril-watcher = {
            harness = "claude";
            model = "sonnet";
            inherit (config.programs.ril.watcher) skillDirectories;
          };
        };
    };
  };
}
