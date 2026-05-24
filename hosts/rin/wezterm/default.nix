{ lib, config, ... }:
{
  config = lib.mkIf (config.homebrew.enable or false) {
    assertions = [
      {
        assertion = lib.any (
          caskEntry: (if builtins.isString caskEntry then caskEntry else (caskEntry.name or "")) == "wezterm"
        ) (config.homebrew.casks or [ ]);
        message = "wezterm must be in homebrew.casks (migrated from HM so its Apple Developer ID signature is stable across rebuilds, preventing repeated Screen Recording TCC re-prompts)";
      }
    ];
  };
}
